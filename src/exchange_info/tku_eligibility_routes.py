"""Public, deterministic TKU home-rule check; no nomination or application action."""
from typing import Literal

from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .tku_data import load_tku_records
from .tku_eligibility import assess_tku_eligibility

ROUND = 'jp-2027-2028-round-2'


class TKUEligibilityRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    round_id: str = Field(default=ROUND, max_length=160)
    partner_id: Literal['ritsumeikan', 'nagasaki', 'seikei', 'uec'] = 'seikei'
    academic_average: float | None = Field(default=None, ge=0, le=100)
    department_top_percent: float | None = Field(default=None, gt=0, le=100)
    degree_level: str | None = Field(default=None, max_length=80)
    year_of_study: int | None = Field(default=None, ge=1, le=6)
    jlpt_level: Literal['N1', 'N2', 'N3', 'N4', 'N5'] | None = None


def register_tku_eligibility_routes(app: FastAPI):
    @app.get('/tku/partner-census')
    def partner_census():
        from .tku_census import census_summary
        return census_summary()

    @app.get('/tku/partner-census/{institution_id}')
    def partner_census_school(institution_id: str):
        from .tku_census import school_audit_by_id
        row=school_audit_by_id(institution_id)
        if row is None:raise HTTPException(status_code=404,detail='此機構不在淡江全量名錄／甄選清單聯集中。')
        return row

    @app.post('/tku/eligibility-check')
    def eligibility_check(payload: TKUEligibilityRequest, response: Response):
        partner_id = f'{ROUND}-{payload.partner_id}'
        result = assess_tku_eligibility(**payload.model_dump(exclude={'partner_id'}), partner_id=partner_id)
        response.headers['Cache-Control'] = 'no-store'
        if payload.round_id != ROUND:
            return dict(**result, requested_round_id=payload.round_id,
                academic_year=None, application_round=None, checked_at='2026-10-08',
                purpose='未核實此年度梯次；不引用已核實梯次的條件或證據。', evidence=[])
        record = next(r for r in load_tku_records() if r.id == partner_id)
        return dict(**result, academic_year='2027-2028', application_round='日語組第二次甄選',
            checked_at='2026-10-08', purpose='母校已知條件；外校資格、推薦、學制及課程另查。',
            evidence=[e.model_dump(mode='json') for key in ['home_eligibility', 'home_language', 'department_scope']
                      for e in record.fields[key].evidence])
