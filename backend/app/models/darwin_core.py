"""
Darwin Core Models for EMODnet/EurOBIS Export

Implements the Darwin Core Archive (DwC-A) star schema:
- Event Core: Dive events
- Occurrence Extension: Turtle sightings/detections
- ExtendedMeasurementOrFact (eMoF): Sensor measurements

Based on:
- OBIS-ENV-DATA schema
- EMODnet Biology data format requirements
- Darwin Core for biologging recommendations
"""

from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


# WoRMS LSIDs for sea turtle species
TURTLE_SPECIES_LSID = {
    "green": "urn:lsid:marinespecies.org:taxname:137206",
    "loggerhead": "urn:lsid:marinespecies.org:taxname:137205",
    "leatherback": "urn:lsid:marinespecies.org:taxname:137209",
    "hawksbill": "urn:lsid:marinespecies.org:taxname:137207",
    "olive_ridley": "urn:lsid:marinespecies.org:taxname:137208",
    "kemp_ridley": "urn:lsid:marinespecies.org:taxname:137210",
    "flatback": "urn:lsid:marinespecies.org:taxname:137211",
}

TURTLE_SCIENTIFIC_NAMES = {
    "green": "Chelonia mydas",
    "loggerhead": "Caretta caretta",
    "leatherback": "Dermochelys coriacea",
    "hawksbill": "Eretmochelys imbricata",
    "olive_ridley": "Lepidochelys olivacea",
    "kemp_ridley": "Lepidochelys kempii",
    "flatback": "Natator depressus",
}


class DwCEvent(BaseModel):
    """
    Darwin Core Event record (Core table).

    Represents a dive event for a tracked turtle.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Event identifiers
    eventID: Annotated[
        str,
        Field(description="Unique identifier for the event (dive)"),
    ]

    parentEventID: Annotated[
        str | None,
        Field(default=None, description="Identifier for parent event (turtle tracking session)"),
    ]

    # Event metadata
    eventType: Annotated[
        str,
        Field(default="dive", description="Type of event"),
    ]

    eventDate: Annotated[
        str,
        Field(description="ISO 8601 date/time of event start"),
    ]

    eventRemarks: Annotated[
        str | None,
        Field(default=None, description="Comments about the event"),
    ]

    # Location
    decimalLatitude: Annotated[
        float,
        Field(ge=-90, le=90, description="Latitude in decimal degrees"),
    ]

    decimalLongitude: Annotated[
        float,
        Field(ge=-180, le=180, description="Longitude in decimal degrees"),
    ]

    geodeticDatum: Annotated[
        str,
        Field(default="EPSG:4326", description="Spatial reference system"),
    ]

    coordinateUncertaintyInMeters: Annotated[
        float | None,
        Field(default=None, description="Uncertainty radius in meters"),
    ]

    # Depth
    minimumDepthInMeters: Annotated[
        float | None,
        Field(default=None, ge=0, description="Minimum depth during event"),
    ]

    maximumDepthInMeters: Annotated[
        float | None,
        Field(default=None, ge=0, description="Maximum depth during event"),
    ]

    # Sampling
    samplingProtocol: Annotated[
        str,
        Field(
            default="satellite telemetry biologging",
            description="Sampling methodology",
        ),
    ]

    sampleSizeValue: Annotated[
        int | None,
        Field(default=None, description="Number of samples in event"),
    ]

    sampleSizeUnit: Annotated[
        str | None,
        Field(default=None, description="Unit of sample size"),
    ]

    # Dataset
    datasetID: Annotated[
        str | None,
        Field(default=None, description="Dataset identifier"),
    ]

    datasetName: Annotated[
        str | None,
        Field(default=None, description="Dataset name"),
    ]

    institutionCode: Annotated[
        str | None,
        Field(default=None, description="Institution code"),
    ]


class DwCOccurrence(BaseModel):
    """
    Darwin Core Occurrence record (Extension table).

    Represents a turtle occurrence/detection linked to a dive event.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Identifiers
    occurrenceID: Annotated[
        str,
        Field(description="Unique identifier for this occurrence"),
    ]

    eventID: Annotated[
        str,
        Field(description="Reference to parent event"),
    ]

    # Organism
    organismID: Annotated[
        str,
        Field(description="Identifier for the individual organism (turtle)"),
    ]

    organismName: Annotated[
        str | None,
        Field(default=None, description="Name given to the organism"),
    ]

    # Taxonomy
    scientificName: Annotated[
        str,
        Field(description="Full scientific name"),
    ]

    scientificNameID: Annotated[
        str,
        Field(description="WoRMS LSID for the species"),
    ]

    kingdom: Annotated[
        str,
        Field(default="Animalia", description="Taxonomic kingdom"),
    ]

    phylum: Annotated[
        str,
        Field(default="Chordata", description="Taxonomic phylum"),
    ]

    class_: Annotated[
        str,
        Field(default="Reptilia", alias="class", description="Taxonomic class"),
    ]

    order: Annotated[
        str,
        Field(default="Testudines", description="Taxonomic order"),
    ]

    family: Annotated[
        str,
        Field(default="Cheloniidae", description="Taxonomic family"),
    ]

    taxonRank: Annotated[
        str,
        Field(default="species", description="Taxonomic rank"),
    ]

    # Occurrence details
    occurrenceStatus: Annotated[
        str,
        Field(default="present", description="Presence/absence status"),
    ]

    basisOfRecord: Annotated[
        str,
        Field(default="MachineObservation", description="Nature of the record"),
    ]

    # Recording
    recordedBy: Annotated[
        str | None,
        Field(default=None, description="Person or system that recorded"),
    ]

    occurrenceRemarks: Annotated[
        str | None,
        Field(default=None, description="Comments about the occurrence"),
    ]


class DwCMeasurementOrFact(BaseModel):
    """
    Darwin Core ExtendedMeasurementOrFact record (eMoF Extension).

    Represents sensor measurements (temperature, depth, pressure).
    """

    model_config = ConfigDict(populate_by_name=True)

    # Identifiers
    measurementID: Annotated[
        str,
        Field(description="Unique identifier for this measurement"),
    ]

    eventID: Annotated[
        str | None,
        Field(default=None, description="Reference to event"),
    ]

    occurrenceID: Annotated[
        str | None,
        Field(default=None, description="Reference to occurrence"),
    ]

    # Measurement
    measurementType: Annotated[
        str,
        Field(description="Type of measurement"),
    ]

    measurementTypeID: Annotated[
        str,
        Field(description="URI for measurement type vocabulary"),
    ]

    measurementValue: Annotated[
        str,
        Field(description="Value of the measurement"),
    ]

    measurementValueID: Annotated[
        str | None,
        Field(default=None, description="URI for measurement value vocabulary"),
    ]

    measurementUnit: Annotated[
        str,
        Field(description="Unit of measurement"),
    ]

    measurementUnitID: Annotated[
        str,
        Field(description="URI for unit vocabulary"),
    ]

    # Timestamp
    measurementDeterminedDate: Annotated[
        str | None,
        Field(default=None, description="ISO 8601 date of measurement"),
    ]

    measurementMethod: Annotated[
        str | None,
        Field(default=None, description="Method used for measurement"),
    ]

    measurementRemarks: Annotated[
        str | None,
        Field(default=None, description="Comments about the measurement"),
    ]


# NERC/BODC vocabulary URIs for measurements
MEASUREMENT_TYPES = {
    "temperature": {
        "type": "Water temperature",
        "typeID": "http://vocab.nerc.ac.uk/collection/P01/current/TEMPPR01/",
        "unit": "degrees Celsius",
        "unitID": "http://vocab.nerc.ac.uk/collection/P06/current/UPAA/",
    },
    "depth": {
        "type": "Depth below surface of the water body",
        "typeID": "http://vocab.nerc.ac.uk/collection/P01/current/ADEPZZ01/",
        "unit": "metres",
        "unitID": "http://vocab.nerc.ac.uk/collection/P06/current/ULAA/",
    },
    "pressure": {
        "type": "Pressure (measured variable) in the water body",
        "typeID": "http://vocab.nerc.ac.uk/collection/P01/current/PRESPR01/",
        "unit": "hectopascals",
        "unitID": "http://vocab.nerc.ac.uk/collection/P06/current/HPAX/",
    },
}


class DwCArchiveExport(BaseModel):
    """Complete Darwin Core Archive export structure."""

    events: list[DwCEvent]
    occurrences: list[DwCOccurrence]
    measurements: list[DwCMeasurementOrFact]

    # Metadata
    export_date: datetime
    record_count: dict[str, int]


class ExportRequest(BaseModel):
    """Request parameters for data export."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "turtle_ids": ["TRT-2024-001"],
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "include_samples": True,
                "dataset_name": "Sea Turtle Tracking Project",
                "institution_code": "HES-SO and University of Bern/BFH master",
            }
        }
    )

    turtle_ids: Annotated[
        list[str] | None,
        Field(default=None, description="Filter by turtle IDs (all if not specified)"),
    ]

    start_date: Annotated[
        datetime | None,
        Field(default=None, description="Start date filter"),
    ]

    end_date: Annotated[
        datetime | None,
        Field(default=None, description="End date filter"),
    ]

    include_samples: Annotated[
        bool,
        Field(default=True, description="Include individual sample measurements"),
    ]

    dataset_name: Annotated[
        str,
        Field(default="PI MONIT Sea Turtle Tracking", description="Dataset name"),
    ]

    institution_code: Annotated[
        str,
        Field(default="HEIG-VD", description="Institution code"),
    ]
