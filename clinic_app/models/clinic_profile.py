"""
Clinic configuration and default clinic/doctor constants
matching the exact physical letterhead of B.D. Medical Centre.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DoctorInfo:
    name: str
    qualifications: str
    regn_no: str


@dataclass
class ClinicProfile:
    name: str = "B.D. Medical Centre"
    address: str = "B-236, Sector 19, Dwarka, New Delhi - 110075"
    phones: str = "9211222255, 9213401340"
    timings: str = "Monday to Saturday, Morning 9:30 am to 1:30 pm, Evening : 6:00 pm to 8:00 pm"
    closed_days: str = "Sunday Closed"
    logo_filename: str = "logo.png"

    # Doctors listed on letterhead
    doctor_left: DoctorInfo = field(
        default_factory=lambda: DoctorInfo(
            name="Dr. Gaurav Sachdev",
            qualifications="M.B.B.S., D.P.M.R.",
            regn_no="DMC Regn No. 4482",
        )
    )
    doctor_right: DoctorInfo = field(
        default_factory=lambda: DoctorInfo(
            name="Dr. Anku Sachdev",
            qualifications="M.B.B.S.",
            regn_no="DMC Regn No. 10590",
        )
    )


# Default singleton profile instance
DEFAULT_CLINIC_PROFILE = ClinicProfile()
