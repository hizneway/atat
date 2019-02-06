from enum import Enum
from datetime import date

import pendulum
from sqlalchemy import Column, Numeric, String, ForeignKey, Date, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import ARRAY
from sqlalchemy.orm import relationship
from werkzeug.datastructures import FileStorage

from atst.models import Attachment, Base, types, mixins


class Status(Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    EXPIRED = "Expired"


class TaskOrder(Base, mixins.TimestampsMixin):
    __tablename__ = "task_orders"

    id = types.Id()

    portfolio_id = Column(ForeignKey("portfolios.id"))
    portfolio = relationship("Portfolio")

    user_id = Column(ForeignKey("users.id"))
    creator = relationship("User", foreign_keys="TaskOrder.user_id")

    ko_id = Column(ForeignKey("users.id"))
    contracting_officer = relationship("User", foreign_keys="TaskOrder.ko_id")

    cor_id = Column(ForeignKey("users.id"))
    contracting_officer_representative = relationship(
        "User", foreign_keys="TaskOrder.cor_id"
    )

    so_id = Column(ForeignKey("users.id"))
    security_officer = relationship("User", foreign_keys="TaskOrder.so_id")

    scope = Column(String)  # Cloud Project Scope
    defense_component = Column(String)  # Department of Defense Component
    app_migration = Column(String)  # App Migration
    native_apps = Column(String)  # Native Apps
    complexity = Column(ARRAY(String))  # Application Complexity
    complexity_other = Column(String)
    dev_team = Column(ARRAY(String))  # Development Team
    dev_team_other = Column(String)
    team_experience = Column(String)  # Team Experience
    start_date = Column(Date)  # Period of Performance
    end_date = Column(Date)
    performance_length = Column(Integer)
    csp_attachment_id = Column(ForeignKey("attachments.id"))
    _csp_estimate = relationship("Attachment", foreign_keys=[csp_attachment_id])
    clin_01 = Column(Numeric(scale=2))
    clin_02 = Column(Numeric(scale=2))
    clin_03 = Column(Numeric(scale=2))
    clin_04 = Column(Numeric(scale=2))
    ko_first_name = Column(String)  # First Name
    ko_last_name = Column(String)  # Last Name
    ko_email = Column(String)  # Email
    ko_phone_number = Column(String)  # Phone Number
    ko_dod_id = Column(String)  # DOD ID
    cor_first_name = Column(String)  # First Name
    cor_last_name = Column(String)  # Last Name
    cor_email = Column(String)  # Email
    cor_phone_number = Column(String)  # Phone Number
    cor_dod_id = Column(String)  # DOD ID
    so_first_name = Column(String)  # First Name
    so_last_name = Column(String)  # Last Name
    so_email = Column(String)  # Email
    so_phone_number = Column(String)  # Phone Number
    so_dod_id = Column(String)  # DOD ID
    pdf_attachment_id = Column(ForeignKey("attachments.id"))
    _pdf = relationship("Attachment", foreign_keys=[pdf_attachment_id])
    number = Column(String, unique=True)  # Task Order Number
    loa = Column(String)  # Line of Accounting (LOA)
    custom_clauses = Column(String)  # Custom Clauses

    @hybrid_property
    def csp_estimate(self):
        return self._csp_estimate

    @csp_estimate.setter
    def csp_estimate(self, new_csp_estimate):
        if not self._set_attachment_type(new_csp_estimate, "_csp_estimate"):
            raise TypeError("Could not set csp_estimate with invalid type")

    @hybrid_property
    def pdf(self):
        return self._pdf

    @pdf.setter
    def pdf(self, new_pdf):
        if not self._set_attachment_type(new_pdf, "_pdf"):
            raise TypeError("Could not set pdf with invalid type")

    def _set_attachment_type(self, new_attachment, property):
        if isinstance(new_attachment, Attachment):
            setattr(self, property, new_attachment)
            return True
        elif isinstance(new_attachment, FileStorage):
            setattr(
                self, property, Attachment.attach(new_attachment, "task_order", self.id)
            )
            return True
        elif not new_attachment and hasattr(self, property):
            setattr(self, property, None)
            return True
        else:
            return False

    @property
    def is_submitted(self):

        return (
            self.number is not None
            and self.start_date is not None
            and self.end_date is not None
        )

    @property
    def status(self):
        if self.is_submitted:
            now = pendulum.now().date()
            if self.start_date > now:
                return Status.PENDING
            elif self.end_date < now:
                return Status.EXPIRED
            return Status.ACTIVE
        else:
            return Status.PENDING

    @property
    def display_status(self):
        return self.status.value

    @property
    def days_to_expiration(self):
        if self.end_date:
            return (self.end_date - date.today()).days

    @property
    def budget(self):
        return sum(
            filter(None, [self.clin_01, self.clin_02, self.clin_03, self.clin_04])
        )

    @property
    def balance(self):
        # TODO: somehow calculate the remaining balance. For now, assume $0 spent
        return self.budget

    @property
    def portfolio_name(self):
        return self.portfolio.name

    @property
    def is_pending(self):
        return self.status == Status.PENDING

    def to_dictionary(self):
        return {
            "portfolio_name": self.portfolio_name,
            **{
                c.name: getattr(self, c.name)
                for c in self.__table__.columns
                if c.name not in ["id"]
            },
        }

    def __repr__(self):
        return "<TaskOrder(number='{}', budget='{}', end_date='{}', id='{}')>".format(
            self.number, self.budget, self.end_date, self.id
        )
