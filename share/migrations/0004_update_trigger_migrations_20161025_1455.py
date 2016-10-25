# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-10-25 14:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0002_create_share_user'),
        ('share', '0003_unique_organization_institution_names'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_extradata_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_extradataversion(persistent_id, action, change_id, data, date_created, date_modified, same_as_id, same_as_version_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.data, NEW.date_created, NEW.date_modified, NEW.same_as_id, NEW.same_as_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_extradata_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_extradata_change ON share_extradata;\n\n        CREATE TRIGGER share_extradata_change\n        BEFORE INSERT OR UPDATE ON share_extradata\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_extradata_change();',
            reverse_sql='DROP TRIGGER share_extradata_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_venue_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_venueversion(persistent_id, action, change_id, community_identifier, date_created, date_modified, extra_id, extra_version_id, location, name, same_as_id, same_as_version_id, venue_type) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.community_identifier, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.location, NEW.name, NEW.same_as_id, NEW.same_as_version_id, NEW.venue_type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_venue_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_venue_change ON share_venue;\n\n        CREATE TRIGGER share_venue_change\n        BEFORE INSERT OR UPDATE ON share_venue\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_venue_change();',
            reverse_sql='DROP TRIGGER share_venue_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_tag_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_tagversion(persistent_id, action, change_id, date_created, date_modified, extra_id, extra_version_id, name, same_as_id, same_as_version_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.name, NEW.same_as_id, NEW.same_as_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_tag_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_tag_change ON share_tag;\n\n        CREATE TRIGGER share_tag_change\n        BEFORE INSERT OR UPDATE ON share_tag\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_tag_change();',
            reverse_sql='DROP TRIGGER share_tag_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_throughvenues_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_throughvenuesversion(persistent_id, action, change_id, creative_work_id, creative_work_version_id, date_created, date_modified, extra_id, extra_version_id, same_as_id, same_as_version_id, venue_id, venue_version_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.creative_work_id, NEW.creative_work_version_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.venue_id, NEW.venue_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_throughvenues_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_throughvenues_change ON share_throughvenues;\n\n        CREATE TRIGGER share_throughvenues_change\n        BEFORE INSERT OR UPDATE ON share_throughvenues\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_throughvenues_change();',
            reverse_sql='DROP TRIGGER share_throughvenues_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_throughtags_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_throughtagsversion(persistent_id, action, change_id, creative_work_id, creative_work_version_id, date_created, date_modified, extra_id, extra_version_id, same_as_id, same_as_version_id, tag_id, tag_version_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.creative_work_id, NEW.creative_work_version_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.tag_id, NEW.tag_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_throughtags_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_throughtags_change ON share_throughtags;\n\n        CREATE TRIGGER share_throughtags_change\n        BEFORE INSERT OR UPDATE ON share_throughtags\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_throughtags_change();',
            reverse_sql='DROP TRIGGER share_throughtags_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_throughsubjects_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_throughsubjectsversion(persistent_id, action, change_id, creative_work_id, creative_work_version_id, date_created, date_modified, extra_id, extra_version_id, same_as_id, same_as_version_id, subject_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.creative_work_id, NEW.creative_work_version_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.subject_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_throughsubjects_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_throughsubjects_change ON share_throughsubjects;\n\n        CREATE TRIGGER share_throughsubjects_change\n        BEFORE INSERT OR UPDATE ON share_throughsubjects\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_throughsubjects_change();',
            reverse_sql='DROP TRIGGER share_throughsubjects_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_agent_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_agentversion(persistent_id, action, additional_name, change_id, date_created, date_modified, extra_id, extra_version_id, family_name, given_name, location, name, same_as_id, same_as_version_id, suffix, type) VALUES (NEW.id, TG_OP, NEW.additional_name, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.family_name, NEW.given_name, NEW.location, NEW.name, NEW.same_as_id, NEW.same_as_version_id, NEW.suffix, NEW.type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_agent_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_agent_change ON share_agent;\n\n        CREATE TRIGGER share_agent_change\n        BEFORE INSERT OR UPDATE ON share_agent\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_agent_change();',
            reverse_sql='DROP TRIGGER share_agent_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_creativework_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_creativeworkversion(persistent_id, action, change_id, date_created, date_modified, date_published, date_updated, description, extra_id, extra_version_id, free_to_read_date, free_to_read_type, is_deleted, language, rights, same_as_id, same_as_version_id, title, type) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.date_published, NEW.date_updated, NEW.description, NEW.extra_id, NEW.extra_version_id, NEW.free_to_read_date, NEW.free_to_read_type, NEW.is_deleted, NEW.language, NEW.rights, NEW.same_as_id, NEW.same_as_version_id, NEW.title, NEW.type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_creativework_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_creativework_change ON share_creativework;\n\n        CREATE TRIGGER share_creativework_change\n        BEFORE INSERT OR UPDATE ON share_creativework\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_creativework_change();',
            reverse_sql='DROP TRIGGER share_creativework_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_workidentifier_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_workidentifierversion(persistent_id, action, change_id, creative_work_id, creative_work_version_id, date_created, date_modified, extra_id, extra_version_id, host, same_as_id, same_as_version_id, scheme, uri) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.creative_work_id, NEW.creative_work_version_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.host, NEW.same_as_id, NEW.same_as_version_id, NEW.scheme, NEW.uri) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_workidentifier_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_workidentifier_change ON share_workidentifier;\n\n        CREATE TRIGGER share_workidentifier_change\n        BEFORE INSERT OR UPDATE ON share_workidentifier\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_workidentifier_change();',
            reverse_sql='DROP TRIGGER share_workidentifier_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_agentidentifier_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_agentidentifierversion(persistent_id, action, agent_id, agent_version_id, change_id, date_created, date_modified, extra_id, extra_version_id, host, same_as_id, same_as_version_id, scheme, uri) VALUES (NEW.id, TG_OP, NEW.agent_id, NEW.agent_version_id, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.host, NEW.same_as_id, NEW.same_as_version_id, NEW.scheme, NEW.uri) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_agentidentifier_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_agentidentifier_change ON share_agentidentifier;\n\n        CREATE TRIGGER share_agentidentifier_change\n        BEFORE INSERT OR UPDATE ON share_agentidentifier\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_agentidentifier_change();',
            reverse_sql='DROP TRIGGER share_agentidentifier_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_agentworkrelation_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_agentworkrelationversion(persistent_id, action, agent_id, agent_version_id, change_id, cited_as, creative_work_id, creative_work_version_id, date_created, date_modified, extra_id, extra_version_id, order_cited, same_as_id, same_as_version_id, type) VALUES (NEW.id, TG_OP, NEW.agent_id, NEW.agent_version_id, NEW.change_id, NEW.cited_as, NEW.creative_work_id, NEW.creative_work_version_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.order_cited, NEW.same_as_id, NEW.same_as_version_id, NEW.type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_agentworkrelation_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_agentworkrelation_change ON share_agentworkrelation;\n\n        CREATE TRIGGER share_agentworkrelation_change\n        BEFORE INSERT OR UPDATE ON share_agentworkrelation\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_agentworkrelation_change();',
            reverse_sql='DROP TRIGGER share_agentworkrelation_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_throughcontributor_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_throughcontributorversion(persistent_id, action, change_id, date_created, date_modified, extra_id, extra_version_id, related_id, related_version_id, same_as_id, same_as_version_id, subject_id, subject_version_id) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.related_id, NEW.related_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.subject_id, NEW.subject_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_throughcontributor_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_throughcontributor_change ON share_throughcontributor;\n\n        CREATE TRIGGER share_throughcontributor_change\n        BEFORE INSERT OR UPDATE ON share_throughcontributor\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_throughcontributor_change();',
            reverse_sql='DROP TRIGGER share_throughcontributor_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_award_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_awardversion(persistent_id, action, change_id, date_created, date_modified, description, extra_id, extra_version_id, name, same_as_id, same_as_version_id, uri) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.description, NEW.extra_id, NEW.extra_version_id, NEW.name, NEW.same_as_id, NEW.same_as_version_id, NEW.uri) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_award_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_award_change ON share_award;\n\n        CREATE TRIGGER share_award_change\n        BEFORE INSERT OR UPDATE ON share_award\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_award_change();',
            reverse_sql='DROP TRIGGER share_award_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_throughawards_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_throughawardsversion(persistent_id, action, award_id, award_version_id, change_id, date_created, date_modified, extra_id, extra_version_id, funder_id, funder_version_id, same_as_id, same_as_version_id) VALUES (NEW.id, TG_OP, NEW.award_id, NEW.award_version_id, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.funder_id, NEW.funder_version_id, NEW.same_as_id, NEW.same_as_version_id) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_throughawards_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_throughawards_change ON share_throughawards;\n\n        CREATE TRIGGER share_throughawards_change\n        BEFORE INSERT OR UPDATE ON share_throughawards\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_throughawards_change();',
            reverse_sql='DROP TRIGGER share_throughawards_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_workrelation_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_workrelationversion(persistent_id, action, change_id, date_created, date_modified, extra_id, extra_version_id, related_id, related_version_id, same_as_id, same_as_version_id, subject_id, subject_version_id, type) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.related_id, NEW.related_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.subject_id, NEW.subject_version_id, NEW.type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_workrelation_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_workrelation_change ON share_workrelation;\n\n        CREATE TRIGGER share_workrelation_change\n        BEFORE INSERT OR UPDATE ON share_workrelation\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_workrelation_change();',
            reverse_sql='DROP TRIGGER share_workrelation_change',
        ),
        migrations.RunSQL(
            sql='CREATE OR REPLACE FUNCTION before_share_agentrelation_change() RETURNS trigger AS $$\n        DECLARE\n            vid INTEGER;\n        BEGIN\n            INSERT INTO share_agentrelationversion(persistent_id, action, change_id, date_created, date_modified, extra_id, extra_version_id, related_id, related_version_id, same_as_id, same_as_version_id, subject_id, subject_version_id, type) VALUES (NEW.id, TG_OP, NEW.change_id, NEW.date_created, NEW.date_modified, NEW.extra_id, NEW.extra_version_id, NEW.related_id, NEW.related_version_id, NEW.same_as_id, NEW.same_as_version_id, NEW.subject_id, NEW.subject_version_id, NEW.type) RETURNING (id) INTO vid;\n            NEW.version_id = vid;\n            RETURN NEW;\n        END;\n        $$ LANGUAGE plpgsql;',
            reverse_sql='DROP FUNCTION before_share_agentrelation_change();',
        ),
        migrations.RunSQL(
            sql='DROP TRIGGER IF EXISTS share_agentrelation_change ON share_agentrelation;\n\n        CREATE TRIGGER share_agentrelation_change\n        BEFORE INSERT OR UPDATE ON share_agentrelation\n        FOR EACH ROW\n        EXECUTE PROCEDURE before_share_agentrelation_change();',
            reverse_sql='DROP TRIGGER share_agentrelation_change',
        ),
    ]
