# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from .. import base
from ..base.fields import Text, Date, Boolean, Integer, Json, Array


# Module API

class Record(base.Record):
    _FULL_DATE_FORMATS = [
        '%B %d, %Y',
        '%b %d, %Y'
    ]

    # Config

    table = 'gsk'

    # General

    study_id = Text(primary_key=True)
    study_title = Text()
    patient_level_data = Text()
    clinicaltrials_gov_identifier = Text()
    sponsor = Text()
    collaborators = Text()
    study_recruitment_status = Text()
    generic_name = Text()
    trade_name = Text()
    study_indication = Text()

    # Protocol summary

    first_received = Date(_FULL_DATE_FORMATS)
    last_updated = Date(_FULL_DATE_FORMATS)
    title = Text()
    phase = Text()
    acronym = Text()
    secondary_ids = Array()
    fda_regulated_intervention = Boolean('yes')
    section_801_clinical_trial = Boolean('yes')
    delayed_posting = Boolean('yes')
    ind_ide_protocol = Text()
    ind_ide_grantor = Text()
    ind_ide_number = Text()
    ind_ide_serial_number = Text()
    has_expanded_access = Boolean('yes')
    study_type = Text()
    oversight_authority = Array()
    sponsor = Text()
    collaborators = Array()
    brief_summary = Text()
    detailed_description = Text()
    record_verification_date = Date(_FULL_DATE_FORMATS)
    status = Text()
    why_study_stopped = Text()
    study_start_date = Date('%B %Y')
    study_completion_date = Date('%B %Y')
    study_completion_date_type = Text()
    primary_completion_date = Date('%B %Y')
    primary_completion_date_type = Text()
    primary_purpose = Text()
    study_design = Text()
    time_perspective = Text()
    biospecimen_retention = Text()
    biospecimen_description = Text()
    allocation = Text()
    masking = Text()
    masked_subject = Boolean('yes')
    masked_caregiver = Boolean('yes')
    masked_investigator = Boolean('yes')
    masked_assessor = Boolean('yes')
    study_design_assignment = Text()
    study_classification_endpoint = Text()
    primary_outcomes = Json()
    secondary_outcomes = Json()
    arms = Json()
    interventions = Json()
    conditions = Array()
    keywords = Array()
    study_population = Text()
    sampling_method = Text()
    eligibility_criteria = Text()
    gender = Text()
    minimum_age = Text()
    maximum_age = Text()
    enrollment = Integer()
    enrollment_type = Text()
    healthy_volunteers = Boolean('yes')
    central_contact = Text()
    central_contact_phone = Text()
    central_contact_email = Text()
    overall_study_official = Text()
    overall_study_official_affiliation = Text()
    overall_study_official_role = Text()
    responsible_party_name_official_title = Text()
    responsible_party_organization = Text()

    # Locations

    contact_name = Text()
    contact_phone = Text()
    contact_email = Text()

    # Result summary

    protocol_id = Text()
    clinical_study_id = Text()
    official_study_title = Text()
    phase = Text()
    study_indication_or_diseases = Text()
    generic_name = Text()
    trade_name = Text()
    trade_name_product_name = Text()
    study_indications = Text()
    results_url = Text()

    # Publication

    citation = Text()
    publication_type = Text()
