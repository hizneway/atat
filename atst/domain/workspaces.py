from sqlalchemy.orm.exc import NoResultFound

from atst.database import db
from atst.models.workspace import Workspace
from atst.models.workspace_role import WorkspaceRole
from atst.domain.exceptions import NotFoundError, UnauthorizedError
from atst.domain.roles import Roles
from atst.domain.authz import Authorization
from atst.models.permissions import Permissions


class Workspaces(object):
    @classmethod
    def create(cls, request, name=None):
        name = name or request.id
        workspace = Workspace(request=request, name=name)
        Workspaces._create_workspace_role(request.creator, workspace, "owner")

        db.session.add(workspace)
        db.session.commit()

        return workspace

    @classmethod
    def get(cls, user, workspace_id):
        try:
            workspace = db.session.query(Workspace).filter_by(id=workspace_id).one()
        except NoResultFound:
            raise NotFoundError("workspace")

        if not Authorization.is_in_workspace(user, workspace):
            raise UnauthorizedError(user, "get workspace")

        return workspace

    @classmethod
    def get_for_update(cls, user, workspace_id):
        workspace = Workspaces.get(user, workspace_id)
        if not Authorization.has_workspace_permission(
            user, workspace, Permissions.ADD_APPLICATION_IN_WORKSPACE
        ):
            raise UnauthorizedError(user, "add project")
        return workspace

    @classmethod
    def get_by_request(cls, request):
        try:
            workspace = db.session.query(Workspace).filter_by(request=request).one()
        except NoResultFound:
            raise NotFoundError("workspace")

        return workspace

    @classmethod
    def get_many(cls, user):
        workspaces = (
            db.session.query(Workspace)
            .join(WorkspaceRole)
            .filter(WorkspaceRole.user == user)
            .all()
        )
        return workspaces

    @classmethod
    def _create_workspace_role(cls, user, workspace, role_name):
        role = Roles.get(role_name)
        workspace_role = WorkspaceRole(
            user=user, role=role, workspace=workspace
        )
        db.session.add(workspace_role)
        return workspace_role


class Members(object):
    def __init__(self):
        pass

    @classmethod
    def create(cls, creator_id, body):
        pass

    @classmethod
    def get(cls, request_id):
        pass

    @classmethod
    def get_many(cls, workspace_id):
        return [
            {
                "first_name": "Danny",
                "last_name": "Knight",
                "email": "dknight@thenavy.mil",
                "dod_id": "1257892124",
                "workspace_role": "Developer",
                "status": "Pending",
                "num_projects": "4",
            },
            {
                "first_name": "Mario",
                "last_name": "Hudson",
                "email": "mhudson@thearmy.mil",
                "dod_id": "4357892125",
                "workspace_role": "CCPO",
                "status": "Active",
                "num_projects": "0",
            },
            {
                "first_name": "Louise",
                "last_name": "Greer",
                "email": "lgreer@theairforce.mil",
                "dod_id": "7257892125",
                "workspace_role": "Admin",
                "status": "Pending",
                "num_projects": "43",
            },
        ]

    @classmethod
    def update(cls, request_id, request_delta):
        pass
