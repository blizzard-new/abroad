"""The complete original NUFS packet survives source-queue reconciliation."""
import pytest
from .test_ncu_nufs_kumamoto_ryukoku import test_next3_reference_packets_and_living_content as check_nufs


@pytest.mark.parametrize('width', [390, 1440])
def test_twelfth_preserved_nufs_packet(page, live_server, monkeypatch, width, tmp_path):
    monkeypatch.setenv('NCU_NEXT3_BROWSER_OUT', str(tmp_path / 'browser'))
    check_nufs(page, live_server, width, 'nufs', '名古屋外國語大學',
               '名古屋外國語大學 Nagoya University of Foreign Studies', 'NUFS初次申請與條件附件', 13)
