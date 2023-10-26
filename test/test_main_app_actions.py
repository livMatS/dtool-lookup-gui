import asyncio
import logging
import pytest

@pytest.mark.asyncio
async def test_do_reset_config(app):
    # assert app.get_application_id() == 'de.uni-freiburg.dtool-lookup-gui'

    # (1 - check that app config agrees with expected mock config, optional)
    # 2 - call do_reset_config action
    # 3 - check that config values have actually been reset
    return