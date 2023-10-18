from typing import List, Type

from fastapi import APIRouter, Depends, HTTPException
from fastapi_auth import admin_required

from app.entities.settings import GeneralSetting, GensSetting, ListsSetting, SettingsCol
from app.models.settings import ChangeSetting
from app.repo.settings import SettingsRepo
from app.routers.dependencies import get_settings_repo

router = APIRouter(
    dependencies=[Depends(admin_required)],
)


@router.get(
    "",
    name="gens:get_settings",
)
async def gens_get_settings(
    repo: SettingsRepo = Depends(get_settings_repo),
):
    return {
        "gens": {
            "perm": await repo.perm_to_dict(GensSetting),
            "temp": await repo.temp_to_dict(GensSetting),
        },
        "lists": {
            "perm": await repo.perm_to_dict(ListsSetting),
            "temp": await repo.temp_to_dict(ListsSetting),
        },
        "general": {
            "perm": await repo.perm_to_dict(GeneralSetting),
            "temp": await repo.temp_to_dict(GeneralSetting),
        },
    }


@router.post(
    "",
    name="gens:change_setting",
)
async def gens_change_setting(
    data_in: ChangeSetting,
    repo: SettingsRepo = Depends(get_settings_repo),
):
    section = data_in.section
    setting_cols: List[Type[SettingsCol]] = [
        GensSetting,
        ListsSetting,
        GeneralSetting,
    ]
    for col in setting_cols:
        if col.section() == section:
            setting = getattr(col, data_in.name)
            break
    else:
        raise HTTPException(400, detail="Wrong section")

    if not await repo.change_setting(setting, data_in):
        raise HTTPException(400, detail="Error while changing setting")
