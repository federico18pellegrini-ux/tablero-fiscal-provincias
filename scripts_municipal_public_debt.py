"""Verified public debt stocks; published future schedules remain explicitly partial."""
import hashlib
import json
from decimal import Decimal

def apply_public_debt(municipalities, path):
    data=json.loads(path.read_text(encoding='utf8'))
    root=path.parents[2]
    for record in data['records']:
        assert record['id'] in municipalities
        assert abs(sum(Decimal(str(r['amount'])) for r in record['components'])-Decimal(str(record['consolidated'])))<Decimal('.01')
        for document in record['documents']:
            original=root/document['path']
            assert hashlib.sha256(original.read_bytes()).hexdigest()==document['sha256']
            assert original.stat().st_size==document['bytes']
        assert all(r['year']>2026 for r in record['schedule'])
        assert record['scheduleStatus']=='partial_published'
        municipalities[record['id']]['publicDebt']=record
    return data
