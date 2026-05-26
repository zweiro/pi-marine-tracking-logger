"""
Export Router

Provides endpoints for exporting data in Darwin Core Archive format
for EMODnet/EurOBIS submission.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response, JSONResponse

from app.database import get_database
from app.models.darwin_core import ExportRequest, DwCArchiveExport
from app.services.darwin_core_exporter import DarwinCoreExporter

router = APIRouter(prefix="/export", tags=["export"])


@router.post(
    "/darwin-core",
    response_model=DwCArchiveExport,
    summary="Export data as Darwin Core JSON",
    description="""
    Export turtle tracking data in Darwin Core Archive format (JSON).

    Returns a structured response with:
    - events: Dive events (Event Core)
    - occurrences: Turtle occurrences (Occurrence Extension)
    - measurements: Sensor measurements (eMoF Extension)

    Use this endpoint to preview the data before downloading the ZIP archive.
    """,
)
async def export_darwin_core_json(
    request: ExportRequest,
    db=Depends(get_database),
) -> DwCArchiveExport:
    """Export data as Darwin Core JSON structure."""
    exporter = DarwinCoreExporter(db)
    return await exporter.export(request)


@router.post(
    "/darwin-core/zip",
    summary="Download Darwin Core Archive ZIP",
    description="""
    Export turtle tracking data as a Darwin Core Archive (DwC-A) ZIP file.

    The ZIP contains:
    - event.csv: Event Core table (dive events)
    - occurrence.csv: Occurrence Extension (turtle sightings)
    - emof.csv: ExtendedMeasurementOrFact Extension (sensor measurements)
    - meta.xml: Archive descriptor
    - eml.xml: EML metadata document

    This format is compatible with EMODnet Biology / EurOBIS submission.
    """,
    response_class=Response,
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Darwin Core Archive ZIP file",
        }
    },
)
async def export_darwin_core_zip(
    request: ExportRequest,
    db=Depends(get_database),
) -> Response:
    """Export data as Darwin Core Archive ZIP file."""
    exporter = DarwinCoreExporter(db)
    zip_data = await exporter.export_to_zip(request)

    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"dwca_turtle_tracking_{timestamp}.zip"

    return Response(
        content=zip_data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get(
    "/darwin-core/vocabularies",
    summary="Get Darwin Core vocabularies",
    description="Returns the NERC/BODC vocabulary URIs used for measurements.",
)
async def get_vocabularies() -> dict:
    """Return vocabulary references used in exports."""
    from app.models.darwin_core import (
        MEASUREMENT_TYPES,
        TURTLE_SPECIES_LSID,
        TURTLE_SCIENTIFIC_NAMES,
    )

    return {
        "measurement_types": MEASUREMENT_TYPES,
        "turtle_species": {
            species: {
                "scientific_name": TURTLE_SCIENTIFIC_NAMES[species],
                "lsid": TURTLE_SPECIES_LSID[species],
            }
            for species in TURTLE_SPECIES_LSID
        },
        "references": {
            "darwin_core": "https://dwc.tdwg.org/terms/",
            "obis_env_data": "https://obis.org/manual/dataformat/",
            "nerc_p01": "http://vocab.nerc.ac.uk/collection/P01/current/",
            "nerc_p06": "http://vocab.nerc.ac.uk/collection/P06/current/",
            "worms": "https://www.marinespecies.org/",
        },
    }
