from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import desc
from sqlalchemy.orm import session

from fcs.models import Undertaking, db, OrganizationLog

from fcs.sync import undertakings as undertakings_module

from . import sync_manager
from .auth import cleanup_unused_users
from .bdr import get_bdr_collections

from .fgases import (
    eea_double_check_fgases,
    parse_fgases_undertaking,
    update_bdr_col_name
)


def get_last_update(days, updated_since):
    if updated_since:
        try:
            last_update = datetime.strptime(updated_since, '%d/%m/%Y')
        except ValueError:
            print 'Invalid date format. Please use DD/MM/YYYY'
            return False
    else:
        days = int(days)
        if days > 0:
            last_update = datetime.now() - timedelta(days=days)
        else:
            last = (
                Undertaking.query
                    .order_by(desc(Undertaking.date_updated))
                    .first()
            )
            last_update = last.date_updated - timedelta(
                days=1) if last else None

    print "Using last_update {}".format(last_update)
    return last_update


@sync_manager.command
@sync_manager.option('-u', '--updated', dest='updated_since',
                     help="Date in DD/MM/YYYY format")
def fgases(days=7, updated_since=None):
    from fcs.match import verify_none
    cleanup_unused_users()
    db.session.autoflush = False
    last_update = get_last_update(days, updated_since)
    undertakings = undertakings_module.get_latest_undertakings(
        type_url='/latest/fgasundertakings/',
        updated_since=last_update
    )

    undertakings_count = 0
    batch = []
    for undertaking in undertakings:
        if eea_double_check_fgases(undertaking):
            batch.append(parse_fgases_undertaking(undertaking))
            if undertakings_count % 10 == 1:
                db.session.add_all(batch)
                db.session.commit()
                del batch[:]
            undertakings_count += 1
            # automatically approve undertaking
            current_app.logger.info(
                'Automatically approve {}'.format(
                    undertaking['external_id']))
            verify_none(undertaking['external_id'], 'SYSTEM')

    db.session.add_all(batch)
    db.session.commit()
    del batch[:]
    cleanup_unused_users()
    if isinstance(last_update, datetime):
        last_update = last_update.date()
    log = OrganizationLog(
        organizations=undertakings_count,
        using_last_update=last_update)
    db.session.add(log)
    print undertakings_count, "values"

    db.session.commit()
    return True


@sync_manager.command
@sync_manager.option('-u', '--updated', dest='updated_since',
                     help="Date in DD/MM/YYYY format")
def fgases_debug_noneu(days=7, updated_since=None):
    # returns a list with all NON EU companies without a legal representative
    # import at this level since an import at module level will break
    # due to a circular import between fcs.match and fcs.sync.fgases
    from fcs.match import verify_none

    last_update = get_last_update(days, updated_since)
    undertakings = undertakings_module.get_latest_undertakings(
        type_url='/latest/fgasundertakings/',
        updated_since=last_update
    )

    undertakings_count = 0
    for undertaking in undertakings:
        if undertaking['euLegalRepresentativeCompany'] is None:
            undertaking_address = undertaking.get('address', None)
            if undertaking_address is not None:
                undertaking_country = undertaking_address.get('country', None)
                if undertaking_country is not None:
                    undertaking_country_type = undertaking_country.get('type', None)
                    if undertaking_country_type == 'NONEU_TYPE':
                        undertakings_count += 1
                        print undertaking

    print undertakings_count, "values"
    return True


@sync_manager.command
def sync_collections_title():
    collections = get_bdr_collections()
    if collections:
        colls = {}
        for collection in collections:
            c_id = collection.get('company_id')
            if c_id:
                if not colls.get(c_id):
                    colls[c_id] = collection
                else:
                    print 'Duplicate collection for company_id: {0} have {1}'\
                          ' and found {2}'.format(c_id, colls[c_id], collection)
        undertakings = Undertaking.query.all()
        for undertaking in undertakings:
            ext_id = str(undertaking.external_id)
            title = undertaking.name
            coll = colls.get(ext_id)
            if coll and coll.get('title') != title:
                if update_bdr_col_name(undertaking):
                    print "Updated collection title for: {0}"\
                          .format(ext_id)
    return True
