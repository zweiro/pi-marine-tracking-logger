"""
Darwin Core Archive Exporter Service

Transforms turtle tracking data to Darwin Core Archive format
for EMODnet/EurOBIS submission.
"""

import csv
import io
import zipfile
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.darwin_core import (
    DwCEvent,
    DwCOccurrence,
    DwCMeasurementOrFact,
    DwCArchiveExport,
    ExportRequest,
    TURTLE_SPECIES_LSID,
    TURTLE_SCIENTIFIC_NAMES,
    MEASUREMENT_TYPES,
)


class DarwinCoreExporter:
    """
    Exports turtle tracking data to Darwin Core Archive format.

    Implements the OBIS-ENV-DATA star schema:
    - Event Core: Dive events
    - Occurrence Extension: Turtle sightings
    - ExtendedMeasurementOrFact: Sensor measurements
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def export(self, request: ExportRequest) -> DwCArchiveExport:
        """
        Export data matching the request parameters.

        Args:
            request: Export parameters (turtle_ids, date range, etc.)

        Returns:
            DwCArchiveExport with events, occurrences, and measurements
        """
        # Build query filters
        turtle_filter = {}
        if request.turtle_ids:
            turtle_filter["turtle_id"] = {"$in": request.turtle_ids}

        dive_filter = {}
        if request.turtle_ids:
            dive_filter["turtle_id"] = {"$in": request.turtle_ids}
        if request.start_date:
            dive_filter["start_time"] = {"$gte": request.start_date}
        if request.end_date:
            dive_filter.setdefault("start_time", {})
            dive_filter["start_time"]["$lte"] = request.end_date

        # Fetch turtles
        turtles = {}
        async for turtle in self.db.turtles.find(turtle_filter):
            turtles[turtle["turtle_id"]] = turtle

        # Fetch dives
        dives = []
        async for dive in self.db.dives.find(dive_filter).sort("start_time", 1):
            dives.append(dive)

        # Build Darwin Core records
        events = []
        occurrences = []
        measurements = []

        for dive in dives:
            turtle_id = dive["turtle_id"]
            turtle = turtles.get(turtle_id)

            if not turtle:
                continue

            # Create Event record
            event = self._create_event(dive, request)
            events.append(event)

            # Create Occurrence record
            occurrence = self._create_occurrence(dive, turtle)
            occurrences.append(occurrence)

            # Create Measurement records from dive stats
            dive_measurements = self._create_dive_measurements(dive, event.eventID)
            measurements.extend(dive_measurements)

            # Include individual samples if requested
            if request.include_samples:
                sample_measurements = await self._create_sample_measurements(
                    dive, event.eventID
                )
                measurements.extend(sample_measurements)

        return DwCArchiveExport(
            events=events,
            occurrences=occurrences,
            measurements=measurements,
            export_date=datetime.utcnow(),
            record_count={
                "events": len(events),
                "occurrences": len(occurrences),
                "measurements": len(measurements),
            },
        )

    def _create_event(self, dive: dict, request: ExportRequest) -> DwCEvent:
        """Create a Darwin Core Event from a dive record."""
        dive_id = str(dive["_id"])
        turtle_id = dive["turtle_id"]

        # Get coordinates from start_location
        coords = dive.get("start_location", {}).get("coordinates", [0, 0])
        longitude, latitude = coords[0], coords[1]

        # Format event date as ISO 8601
        start_time = dive.get("start_time")
        if isinstance(start_time, datetime):
            event_date = start_time.isoformat() + "Z"
        else:
            event_date = str(start_time)

        return DwCEvent(
            eventID=f"dive-{dive_id}",
            parentEventID=f"tracking-{turtle_id}",
            eventType="dive",
            eventDate=event_date,
            decimalLatitude=latitude,
            decimalLongitude=longitude,
            coordinateUncertaintyInMeters=100.0,  # Estimated GPS accuracy
            minimumDepthInMeters=0.0,
            maximumDepthInMeters=dive.get("stats", {}).get("max_depth_m"),
            samplingProtocol="satellite telemetry biologging",
            sampleSizeValue=dive.get("stats", {}).get("sample_count"),
            sampleSizeUnit="samples",
            datasetName=request.dataset_name,
            institutionCode=request.institution_code,
        )

    def _create_occurrence(self, dive: dict, turtle: dict) -> DwCOccurrence:
        """Create a Darwin Core Occurrence from dive and turtle records."""
        dive_id = str(dive["_id"])
        turtle_id = turtle["turtle_id"]
        species = turtle.get("species", "green")

        # Get scientific name and LSID
        scientific_name = TURTLE_SCIENTIFIC_NAMES.get(species, "Chelonia mydas")
        scientific_name_id = TURTLE_SPECIES_LSID.get(
            species, TURTLE_SPECIES_LSID["green"]
        )

        # Determine family based on species
        family = "Cheloniidae"
        if species == "leatherback":
            family = "Dermochelyidae"

        return DwCOccurrence(
            occurrenceID=f"occ-{dive_id}",
            eventID=f"dive-{dive_id}",
            organismID=turtle_id,
            organismName=turtle.get("name"),
            scientificName=scientific_name,
            scientificNameID=scientific_name_id,
            family=family,
            basisOfRecord="MachineObservation",
            occurrenceStatus="present",
        )

    def _create_dive_measurements(
        self, dive: dict, event_id: str
    ) -> list[DwCMeasurementOrFact]:
        """Create eMoF records from dive statistics."""
        measurements = []
        stats = dive.get("stats", {})
        dive_id = str(dive["_id"])

        # Max depth measurement
        if stats.get("max_depth_m") is not None:
            measurements.append(
                DwCMeasurementOrFact(
                    measurementID=f"mof-{dive_id}-max-depth",
                    eventID=event_id,
                    measurementType="Maximum depth below surface",
                    measurementTypeID=MEASUREMENT_TYPES["depth"]["typeID"],
                    measurementValue=str(stats["max_depth_m"]),
                    measurementUnit=MEASUREMENT_TYPES["depth"]["unit"],
                    measurementUnitID=MEASUREMENT_TYPES["depth"]["unitID"],
                    measurementMethod="derived from pressure sensor",
                )
            )

        # Mean temperature measurement
        if stats.get("mean_temp_c") is not None:
            measurements.append(
                DwCMeasurementOrFact(
                    measurementID=f"mof-{dive_id}-mean-temp",
                    eventID=event_id,
                    measurementType="Mean water temperature",
                    measurementTypeID=MEASUREMENT_TYPES["temperature"]["typeID"],
                    measurementValue=str(round(stats["mean_temp_c"], 2)),
                    measurementUnit=MEASUREMENT_TYPES["temperature"]["unit"],
                    measurementUnitID=MEASUREMENT_TYPES["temperature"]["unitID"],
                    measurementMethod="biologging temperature sensor",
                )
            )

        # Min temperature
        if stats.get("min_temp_c") is not None:
            measurements.append(
                DwCMeasurementOrFact(
                    measurementID=f"mof-{dive_id}-min-temp",
                    eventID=event_id,
                    measurementType="Minimum water temperature",
                    measurementTypeID=MEASUREMENT_TYPES["temperature"]["typeID"],
                    measurementValue=str(round(stats["min_temp_c"], 2)),
                    measurementUnit=MEASUREMENT_TYPES["temperature"]["unit"],
                    measurementUnitID=MEASUREMENT_TYPES["temperature"]["unitID"],
                    measurementMethod="biologging temperature sensor",
                )
            )

        # Max temperature
        if stats.get("max_temp_c") is not None:
            measurements.append(
                DwCMeasurementOrFact(
                    measurementID=f"mof-{dive_id}-max-temp",
                    eventID=event_id,
                    measurementType="Maximum water temperature",
                    measurementTypeID=MEASUREMENT_TYPES["temperature"]["typeID"],
                    measurementValue=str(round(stats["max_temp_c"], 2)),
                    measurementUnit=MEASUREMENT_TYPES["temperature"]["unit"],
                    measurementUnitID=MEASUREMENT_TYPES["temperature"]["unitID"],
                    measurementMethod="biologging temperature sensor",
                )
            )

        return measurements

    async def _create_sample_measurements(
        self, dive: dict, event_id: str
    ) -> list[DwCMeasurementOrFact]:
        """Create eMoF records from individual samples."""
        measurements = []
        dive_id = dive["_id"]

        async for sample in self.db.samples.find({"metadata.dive_id": dive_id}):
            sample_idx = sample.get("sample_index", 0)
            timestamp = sample.get("timestamp")

            if isinstance(timestamp, datetime):
                measurement_date = timestamp.isoformat() + "Z"
            else:
                measurement_date = str(timestamp) if timestamp else None

            # Temperature measurement
            if sample.get("temperature_c") is not None:
                measurements.append(
                    DwCMeasurementOrFact(
                        measurementID=f"mof-{dive_id}-s{sample_idx}-temp",
                        eventID=event_id,
                        measurementType=MEASUREMENT_TYPES["temperature"]["type"],
                        measurementTypeID=MEASUREMENT_TYPES["temperature"]["typeID"],
                        measurementValue=str(sample["temperature_c"]),
                        measurementUnit=MEASUREMENT_TYPES["temperature"]["unit"],
                        measurementUnitID=MEASUREMENT_TYPES["temperature"]["unitID"],
                        measurementDeterminedDate=measurement_date,
                        measurementMethod="biologging temperature sensor",
                    )
                )

            # Depth measurement
            if sample.get("depth_m") is not None:
                measurements.append(
                    DwCMeasurementOrFact(
                        measurementID=f"mof-{dive_id}-s{sample_idx}-depth",
                        eventID=event_id,
                        measurementType=MEASUREMENT_TYPES["depth"]["type"],
                        measurementTypeID=MEASUREMENT_TYPES["depth"]["typeID"],
                        measurementValue=str(sample["depth_m"]),
                        measurementUnit=MEASUREMENT_TYPES["depth"]["unit"],
                        measurementUnitID=MEASUREMENT_TYPES["depth"]["unitID"],
                        measurementDeterminedDate=measurement_date,
                        measurementMethod="derived from pressure sensor",
                    )
                )

            # Pressure measurement
            if sample.get("pressure_hpa") is not None:
                measurements.append(
                    DwCMeasurementOrFact(
                        measurementID=f"mof-{dive_id}-s{sample_idx}-pressure",
                        eventID=event_id,
                        measurementType=MEASUREMENT_TYPES["pressure"]["type"],
                        measurementTypeID=MEASUREMENT_TYPES["pressure"]["typeID"],
                        measurementValue=str(sample["pressure_hpa"]),
                        measurementUnit=MEASUREMENT_TYPES["pressure"]["unit"],
                        measurementUnitID=MEASUREMENT_TYPES["pressure"]["unitID"],
                        measurementDeterminedDate=measurement_date,
                        measurementMethod="biologging pressure sensor",
                    )
                )

        return measurements

    async def export_to_zip(self, request: ExportRequest) -> bytes:
        """
        Export data as a Darwin Core Archive ZIP file.

        The ZIP contains:
        - event.csv: Event Core
        - occurrence.csv: Occurrence Extension
        - emof.csv: ExtendedMeasurementOrFact Extension
        - meta.xml: Archive descriptor

        Returns:
            ZIP file as bytes
        """
        export = await self.export(request)

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Event CSV
            zf.writestr("event.csv", self._to_csv(export.events, DwCEvent))

            # Occurrence CSV
            zf.writestr("occurrence.csv", self._to_csv(export.occurrences, DwCOccurrence))

            # eMoF CSV
            zf.writestr("emof.csv", self._to_csv(export.measurements, DwCMeasurementOrFact))

            # Meta.xml descriptor
            zf.writestr("meta.xml", self._generate_meta_xml())

            # EML metadata (basic)
            zf.writestr("eml.xml", self._generate_eml_xml(request, export))

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def _to_csv(self, records: list[Any], model_class: type) -> str:
        """Convert Pydantic models to CSV string."""
        if not records:
            return ""

        output = io.StringIO()

        # Get field names from model, handling aliases
        field_names = []
        field_aliases = {}
        for name, field in model_class.model_fields.items():
            alias = field.alias if field.alias else name
            field_names.append(name)
            field_aliases[name] = alias

        # Write CSV with aliases as headers
        writer = csv.DictWriter(
            output,
            fieldnames=[field_aliases[f] for f in field_names],
            extrasaction="ignore",
        )
        writer.writeheader()

        for record in records:
            # Convert to dict using aliases
            row = {}
            for name in field_names:
                alias = field_aliases[name]
                value = getattr(record, name, None)
                row[alias] = value if value is not None else ""
            writer.writerow(row)

        return output.getvalue()

    def _generate_meta_xml(self) -> str:
        """Generate Darwin Core Archive meta.xml descriptor."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/"
         metadata="eml.xml">
  <core encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
        fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Event">
    <files>
      <location>event.csv</location>
    </files>
    <id index="0"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/parentEventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/eventType"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/eventDate"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/eventRemarks"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/decimalLatitude"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/decimalLongitude"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/geodeticDatum"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/coordinateUncertaintyInMeters"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/minimumDepthInMeters"/>
    <field index="10" term="http://rs.tdwg.org/dwc/terms/maximumDepthInMeters"/>
    <field index="11" term="http://rs.tdwg.org/dwc/terms/samplingProtocol"/>
    <field index="12" term="http://rs.tdwg.org/dwc/terms/sampleSizeValue"/>
    <field index="13" term="http://rs.tdwg.org/dwc/terms/sampleSizeUnit"/>
    <field index="14" term="http://rs.tdwg.org/dwc/terms/datasetID"/>
    <field index="15" term="http://rs.tdwg.org/dwc/terms/datasetName"/>
    <field index="16" term="http://rs.tdwg.org/dwc/terms/institutionCode"/>
  </core>
  <extension encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
             fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="http://rs.tdwg.org/dwc/terms/Occurrence">
    <files>
      <location>occurrence.csv</location>
    </files>
    <coreid index="1"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/organismID"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/organismName"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/scientificName"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/scientificNameID"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/kingdom"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/phylum"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/class"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/order"/>
    <field index="10" term="http://rs.tdwg.org/dwc/terms/family"/>
    <field index="11" term="http://rs.tdwg.org/dwc/terms/taxonRank"/>
    <field index="12" term="http://rs.tdwg.org/dwc/terms/occurrenceStatus"/>
    <field index="13" term="http://rs.tdwg.org/dwc/terms/basisOfRecord"/>
    <field index="14" term="http://rs.tdwg.org/dwc/terms/recordedBy"/>
    <field index="15" term="http://rs.tdwg.org/dwc/terms/occurrenceRemarks"/>
  </extension>
  <extension encoding="UTF-8" fieldsTerminatedBy="," linesTerminatedBy="\\n"
             fieldsEnclosedBy="&quot;" ignoreHeaderLines="1" rowType="http://rs.iobis.org/obis/terms/ExtendedMeasurementOrFact">
    <files>
      <location>emof.csv</location>
    </files>
    <coreid index="1"/>
    <field index="0" term="http://rs.tdwg.org/dwc/terms/measurementID"/>
    <field index="1" term="http://rs.tdwg.org/dwc/terms/eventID"/>
    <field index="2" term="http://rs.tdwg.org/dwc/terms/occurrenceID"/>
    <field index="3" term="http://rs.tdwg.org/dwc/terms/measurementType"/>
    <field index="4" term="http://rs.tdwg.org/dwc/terms/measurementTypeID"/>
    <field index="5" term="http://rs.tdwg.org/dwc/terms/measurementValue"/>
    <field index="6" term="http://rs.tdwg.org/dwc/terms/measurementValueID"/>
    <field index="7" term="http://rs.tdwg.org/dwc/terms/measurementUnit"/>
    <field index="8" term="http://rs.tdwg.org/dwc/terms/measurementUnitID"/>
    <field index="9" term="http://rs.tdwg.org/dwc/terms/measurementDeterminedDate"/>
    <field index="10" term="http://rs.tdwg.org/dwc/terms/measurementMethod"/>
    <field index="11" term="http://rs.tdwg.org/dwc/terms/measurementRemarks"/>
  </extension>
</archive>'''

    def _generate_eml_xml(self, request: ExportRequest, export: DwCArchiveExport) -> str:
        """Generate basic EML metadata document."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="eml://ecoinformatics.org/eml-2.1.1 http://rs.gbif.org/schema/eml-gbif-profile/1.1/eml.xsd"
         packageId="pi-monit-turtle-tracking" system="http://gbif.org" scope="system">
  <dataset>
    <title>{request.dataset_name}</title>
    <creator>
      <organizationName>{request.institution_code}</organizationName>
    </creator>
    <pubDate>{export.export_date.strftime("%Y-%m-%d")}</pubDate>
    <abstract>
      <para>Sea turtle biologging data from satellite telemetry tracking.</para>
      <para>Contains {export.record_count["events"]} dive events, {export.record_count["occurrences"]} occurrences, and {export.record_count["measurements"]} measurements.</para>
    </abstract>
    <intellectualRights>
      <para>This work is licensed under a Creative Commons Attribution 4.0 International License.</para>
    </intellectualRights>
  </dataset>
</eml:eml>'''
