-- ============================================================================
-- CAMPUS PLACEMENT ANALYTICS SYSTEM - PHASE 1: MASTER RUN SCRIPT
-- Execute in SQL*Plus or Oracle SQL Developer:
-- SQL> @run_all.sql   (from within database directory)
-- ============================================================================

SET SQLBLANKLINES ON;
SET DEFINE OFF;
SET FEEDBACK ON;
SET SERVEROUTPUT ON;
SET ECHO OFF;

PROMPT =======================================================
PROMPT 1. CREATING TABLES AND CONSTRAINTS...
PROMPT =======================================================
@@01_schema.sql

PROMPT =======================================================
PROMPT 2. INSERTING SAMPLE SEED DATA...
PROMPT =======================================================
@@02_seed_data.sql

PROMPT =======================================================
PROMPT 3. EXECUTING ANALYTICAL AND VERIFICATION QUERIES...
PROMPT =======================================================
@@03_queries.sql

PROMPT =======================================================
PROMPT 4. EXECUTING PHASE 7 ADVANCED ANALYTICS QUERIES...
PROMPT =======================================================
@@04_analytics_queries.sql

PROMPT =======================================================
PROMPT CAMPUS PLACEMENT DATABASE SETUP COMPLETE!
PROMPT =======================================================

