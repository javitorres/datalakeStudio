from fastapi import APIRouter
from fastapi.responses import JSONResponse

from model.DashboardDTO import DashboardDTO, PublishDashboardDTO, PublishedQueryDTO
from services import dashboardsService, databaseService

# The user's own dashboards
router = APIRouter(prefix="/dashboards")
# The published ones, by their path: /d/iris/flower_analysis
published_router = APIRouter(prefix="/d")


def _error(message, status_code):
    return JSONResponse(content={"status": "error", "message": message}, status_code=status_code)


def _not_found(what):
    return _error(f"Dashboard {what} not found", 404)


@router.get("")
def listDashboards():
    return dashboardsService.list_dashboards()


@router.get("/{dashboard_id}")
def getDashboard(dashboard_id: str):
    try:
        dashboard = dashboardsService.get_dashboard(dashboard_id)
    except ValueError as e:
        return _error(str(e), 400)
    return dashboard if dashboard is not None else _not_found(dashboard_id)


@router.put("/{dashboard_id}")
def saveDashboard(dashboard_id: str, dashboard: DashboardDTO):
    try:
        saved = dashboardsService.save_dashboard(
            dashboard_id, dashboard.title, dashboard.spec, dashboard.history,
            dashboard.database or databaseService.get_current_database_name())
    except ValueError as e:
        return _error(str(e), 400)
    return {k: v for k, v in saved.items() if k not in ("spec", "history")}


@router.delete("/{dashboard_id}")
def deleteDashboard(dashboard_id: str):
    try:
        deleted = dashboardsService.delete_dashboard(dashboard_id)
    except ValueError as e:
        return _error(str(e), 400)
    return {"status": "ok"} if deleted else _not_found(dashboard_id)


@router.put("/{dashboard_id}/publish")
def publishDashboard(dashboard_id: str, request: PublishDashboardDTO):
    try:
        published = dashboardsService.publish_dashboard(dashboard_id, request.path, request.queries)
    except dashboardsService.PathTaken as e:
        return _error(str(e), 409)
    except Exception as e:
        # An invalid path, or a query that isn't a SELECT or doesn't run
        return _error(str(e), 400)
    return published if published is not None else _not_found(dashboard_id)


@router.delete("/{dashboard_id}/publish")
def unpublishDashboard(dashboard_id: str):
    try:
        dashboard = dashboardsService.unpublish_dashboard(dashboard_id)
    except ValueError as e:
        return _error(str(e), 400)
    return dashboard if dashboard is not None else _not_found(dashboard_id)


####################################################
@published_router.get("")
def listPublished():
    return dashboardsService.list_published()


@published_router.get("/{path:path}")
def getPublished(path: str):
    try:
        dashboard = dashboardsService.get_published(path)
    except ValueError as e:
        return _error(str(e), 400)
    return dashboard if dashboard is not None else _not_found(path)


@published_router.post("/{path:path}")
def queryPublished(path: str, request: PublishedQueryDTO):
    try:
        rows = dashboardsService.run_published(path, request.query, request.filters)
    except Exception as e:
        return _error(str(e), 400)
    return rows if rows is not None else _not_found(path)
