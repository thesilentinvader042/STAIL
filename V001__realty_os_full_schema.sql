-- ============================================================
-- REALTY OS — Complete Database Migration
-- V001__realty_os_full_schema.sql
-- PostgreSQL 16 + PostGIS + pgvector
-- Run once on a fresh database.
-- ============================================================

-- ── 0. Extensions ────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Schema namespace ─────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS realty_os;
SET search_path TO realty_os, public;

-- ============================================================
-- 1. ENUM TYPES
-- ============================================================

CREATE TYPE property_type_enum AS ENUM (
    'RESIDENTIAL','COMMERCIAL','PLOT','VILLA','WAREHOUSE','COWORKING'
);
CREATE TYPE listing_status_enum AS ENUM (
    'DRAFT','ACTIVE','UNDER_OFFER','SOLD','RENTED','DELISTED','EXPIRED'
);
CREATE TYPE transaction_type_enum AS ENUM (
    'SALE','RENT','LEASE','CO_LEASE','PLOTTED_SALE','LEAVE_LICENSE'
);
CREATE TYPE bhk_type_enum AS ENUM (
    'STUDIO','1RK','1BHK','2BHK','2.5BHK','3BHK','3.5BHK',
    '4BHK','4PLUS_BHK','PENTHOUSE'
);
CREATE TYPE facing_direction_enum AS ENUM (
    'NORTH','SOUTH','EAST','WEST','NE','NW','SE','SW'
);
CREATE TYPE furnishing_status_enum AS ENUM (
    'UNFURNISHED','SEMI_FURNISHED','FULLY_FURNISHED',
    'TURNKEY','PLUG_AND_PLAY','BARE_SHELL','WARM_SHELL'
);
CREATE TYPE possession_status_enum AS ENUM (
    'READY_TO_MOVE','UNDER_CONSTRUCTION','NEW_LAUNCH'
);
CREATE TYPE commercial_grade_enum AS ENUM (
    'GRADE_A_PLUS','GRADE_A','GRADE_B','GRADE_C'
);
CREATE TYPE commercial_occupancy_enum AS ENUM (
    'VACANT','OWNER_OCCUPIED','TENANTED','PARTIAL','BARE_SHELL'
);
CREATE TYPE plot_subtype_enum AS ENUM (
    'RESIDENTIAL','COMMERCIAL','AGRICULTURAL','INDUSTRIAL',
    'INSTITUTIONAL','FARM','NA_CONVERTED'
);
CREATE TYPE zone_type_enum AS ENUM (
    'RESIDENTIAL_ZONE','COMMERCIAL_ZONE','MIXED_USE',
    'INDUSTRIAL','GREEN_ZONE','RESERVED_FOREST'
);
CREATE TYPE warehouse_subtype_enum AS ENUM (
    'GRADE_A','GRADE_B','COLD_STORAGE','MANUFACTURING',
    'SHED','LOGISTICS_PARK','DARK_STORE','SEZ'
);
CREATE TYPE coworking_subtype_enum AS ENUM (
    'HOT_DESK','DEDICATED_DESK','PRIVATE_CABIN','TEAM_SUITE',
    'VIRTUAL_OFFICE','ENTERPRISE_FLOOR','INCUBATOR'
);
CREATE TYPE pricing_model_enum AS ENUM (
    'HOURLY','DAILY','MONTHLY','ANNUAL','PAY_PER_USE'
);
CREATE TYPE offer_status_enum AS ENUM (
    'SUBMITTED','COUNTERED','ACCEPTED','REJECTED','EXPIRED','WITHDRAWN'
);
CREATE TYPE agreement_type_enum AS ENUM (
    'SALE','RENT','LEASE','LEASE_PURCHASE','LEAVE_LICENSE'
);
CREATE TYPE agreement_status_enum AS ENUM (
    'DRAFT','REVIEW','SIGNED','STAMPED','REGISTERED','CANCELLED'
);
CREATE TYPE price_event_type_enum AS ENUM (
    'LISTING_PRICE','PRICE_REDUCTION','PRICE_INCREASE',
    'FINAL_SALE','RENTAL_RATE','LEASE_RATE'
);
CREATE TYPE data_source_enum AS ENUM (
    'PLATFORM_LISTING','SUB_REGISTRAR','RERA',
    'USER_REPORTED','SCRAPED','DEVELOPER_API'
);
CREATE TYPE enquiry_channel_enum AS ENUM (
    'PLATFORM_FORM','WHATSAPP','PHONE','EMAIL',
    'CHATBOT','WALKIN','API'
);
CREATE TYPE enquiry_status_enum AS ENUM (
    'NEW','CONTACTED','VISIT_SCHEDULED','VISITED',
    'NEGOTIATING','CLOSED_WON','CLOSED_LOST','DROPPED'
);
CREATE TYPE rera_status_enum AS ENUM (
    'ACTIVE','EXPIRED','REVOKED','LAPSED','EXTENDED'
);
CREATE TYPE oc_status_enum AS ENUM (
    'NOT_APPLIED','APPLIED','RECEIVED'
);
CREATE TYPE seismic_zone_enum AS ENUM (
    'ZONE_II','ZONE_III','ZONE_IV','ZONE_V'
);
CREATE TYPE flood_risk_enum AS ENUM (
    'LOW','MEDIUM','HIGH'
);
CREATE TYPE fire_suppression_enum AS ENUM (
    'SPRINKLERS','FOAM_SYSTEM','DRY_POWDER','NONE'
);
CREATE TYPE road_type_enum AS ENUM (
    'TARRED','GRAVEL','DIRT','NH','SH','MDR'
);
CREATE TYPE ownership_type_enum AS ENUM (
    'FREEHOLD','LEASEHOLD','GOVT_ALLOTMENT','TRUST','COOPERATIVE_SOCIETY'
);
CREATE TYPE water_source_enum AS ENUM (
    'MUNICIPAL','BOREWELL','TANKER','BOTH_MUNICIPAL_BOREWELL'
);
CREATE TYPE power_backup_enum AS ENUM (
    'NONE','PARTIAL','FULL'
);
CREATE TYPE data_quality_enum AS ENUM (
    'REGISTRY_VERIFIED','PLATFORM_DATA','SPARSE'
);
CREATE TYPE property_source_enum AS ENUM (
    'PLATFORM','API','SCRAPE','IMPORT','DEVELOPER_PORTAL'
);
CREATE TYPE villa_subtype_enum AS ENUM (
    'STANDALONE','ROW_HOUSE','TWIN_BUNGALOW','GATED_COMMUNITY',
    'FARMHOUSE','PENTHOUSE_VILLA'
);
CREATE TYPE commercial_subtype_enum AS ENUM (
    'IT_OFFICE','NON_IT_OFFICE','RETAIL_SHOP','SHOWROOM',
    'MALL_UNIT','MEDICAL','SEZ_UNIT'
);

-- ============================================================
-- 2. SHARED INFRASTRUCTURE TABLES
-- ============================================================

-- ── 2.1 organisations ────────────────────────────────────────
CREATE TABLE organisations (
    organisation_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(200) NOT NULL,
    org_type            VARCHAR(50),           -- DEVELOPER | BROKER_FIRM | OPERATOR
    gstin               VARCHAR(15),
    rera_number         VARCHAR(80),
    website             VARCHAR(300),
    city                VARCHAR(80),
    state_code          CHAR(2),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2.2 users ────────────────────────────────────────────────
CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    phone               VARCHAR(20),
    full_name           VARCHAR(200) NOT NULL,
    hashed_password     VARCHAR(255) NOT NULL,
    role                VARCHAR(30) NOT NULL DEFAULT 'BUYER', -- BUYER|SELLER|BROKER|DEVELOPER|INVESTOR|ADMIN
    organisation_id     UUID REFERENCES organisations(organisation_id),
    rera_agent_number   VARCHAR(100),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser        BOOLEAN NOT NULL DEFAULT FALSE,
    is_nri              BOOLEAN NOT NULL DEFAULT FALSE,
    language_pref       CHAR(5) NOT NULL DEFAULT 'en',
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2.3 locations ────────────────────────────────────────────
CREATE TABLE locations (
    location_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_line_1      VARCHAR(255) NOT NULL,
    address_line_2      VARCHAR(255),
    locality            VARCHAR(120) NOT NULL,
    city                VARCHAR(80)  NOT NULL,
    district            VARCHAR(80),
    state_code          CHAR(2)      NOT NULL,
    pin_code            CHAR(6)      NOT NULL,
    latitude            NUMERIC(10,7),
    longitude           NUMERIC(10,7),
    geo_point           geography(POINT, 4326),
    geo_polygon         geography(POLYGON, 4326),
    sub_district        VARCHAR(80),
    survey_number       VARCHAR(60),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2.4 rera_registrations ────────────────────────────────────
CREATE TABLE rera_registrations (
    rera_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rera_number         VARCHAR(80) NOT NULL UNIQUE,
    state_code          CHAR(2)     NOT NULL,
    project_name        VARCHAR(200) NOT NULL,
    promoter_id         UUID REFERENCES organisations(organisation_id),
    registration_date   DATE        NOT NULL,
    expiry_date         DATE,
    status              rera_status_enum NOT NULL DEFAULT 'ACTIVE',
    last_verified_at    TIMESTAMPTZ,
    occupancy_cert_status oc_status_enum DEFAULT 'NOT_APPLIED',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 2.5 properties (base table) ───────────────────────────────
CREATE TABLE properties (
    property_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_type       property_type_enum  NOT NULL,
    property_subtype    VARCHAR(60),
    listing_status      listing_status_enum NOT NULL DEFAULT 'DRAFT',
    transaction_type    transaction_type_enum NOT NULL,
    title               VARCHAR(255) NOT NULL,
    description         TEXT,
    description_vector  vector(1536),           -- pgvector: semantic search
    location_id         UUID NOT NULL REFERENCES locations(location_id),
    geo_point           geography(POINT, 4326),
    posted_by_user_id   UUID NOT NULL REFERENCES users(user_id),
    organisation_id     UUID REFERENCES organisations(organisation_id),
    rera_id             UUID REFERENCES rera_registrations(rera_id),
    asking_price        NUMERIC(15,2),
    price_currency      CHAR(3)  NOT NULL DEFAULT 'INR',
    price_per_sqft      NUMERIC(10,2),
    carpet_area_sqft    NUMERIC(10,2),
    built_up_area_sqft  NUMERIC(10,2),
    super_built_up      NUMERIC(10,2),
    is_verified         BOOLEAN  NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN  NOT NULL DEFAULT TRUE,
    is_featured         BOOLEAN  NOT NULL DEFAULT FALSE,
    views_count         INTEGER  NOT NULL DEFAULT 0,
    enquiry_count       INTEGER  NOT NULL DEFAULT 0,
    attributes          JSONB    DEFAULT '{}',
    tags                TEXT[]   DEFAULT '{}',
    platform_tenant_id  UUID,
    source              property_source_enum NOT NULL DEFAULT 'PLATFORM',
    posted_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

-- ── auto-update trigger ────────────────────────────────────────
CREATE OR REPLACE FUNCTION realty_os.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_properties_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── price_per_sqft auto-calc trigger ──────────────────────────
CREATE OR REPLACE FUNCTION realty_os.calc_price_per_sqft()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.asking_price IS NOT NULL AND NEW.carpet_area_sqft IS NOT NULL
       AND NEW.carpet_area_sqft > 0 THEN
        NEW.price_per_sqft := ROUND(NEW.asking_price / NEW.carpet_area_sqft, 2);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calc_price_psf
    BEFORE INSERT OR UPDATE OF asking_price, carpet_area_sqft ON properties
    FOR EACH ROW EXECUTE FUNCTION calc_price_per_sqft();

-- ============================================================
-- 3. RESIDENTIAL PROPERTIES
-- ============================================================
CREATE TABLE residential_properties (
    residential_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id             UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    bhk_type                bhk_type_enum NOT NULL,
    num_bedrooms            SMALLINT NOT NULL CHECK (num_bedrooms >= 0),
    num_bathrooms           SMALLINT NOT NULL CHECK (num_bathrooms >= 0),
    num_balconies           SMALLINT,
    floor_number            SMALLINT,
    total_floors            SMALLINT,
    tower_name              VARCHAR(80),
    unit_number             VARCHAR(20),
    facing_direction        facing_direction_enum,
    furnishing_status       furnishing_status_enum NOT NULL,
    possession_status       possession_status_enum NOT NULL,
    possession_date         DATE,
    age_of_property_yrs     SMALLINT,
    parking_covered         SMALLINT DEFAULT 0,
    parking_open            SMALLINT DEFAULT 0,
    pooja_room              BOOLEAN DEFAULT FALSE,
    servant_room            BOOLEAN DEFAULT FALSE,
    study_room              BOOLEAN DEFAULT FALSE,
    store_room              BOOLEAN DEFAULT FALSE,
    is_vastu_compliant      BOOLEAN DEFAULT FALSE,
    is_corner_unit          BOOLEAN DEFAULT FALSE,
    has_terrace             BOOLEAN DEFAULT FALSE,
    water_source            water_source_enum,
    power_backup            power_backup_enum,
    project_id              UUID,               -- FK to developer_projects (add when that table exists)
    society_id              UUID,               -- FK to societies
    monthly_maintenance     NUMERIC(8,2),
    floor_plan_url          VARCHAR(500),
    virtual_tour_url        VARCHAR(500),
    amenity_ids             UUID[]  DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_residential_updated_at
    BEFORE UPDATE ON residential_properties
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 4. COMMERCIAL PROPERTIES
-- ============================================================
CREATE TABLE commercial_properties (
    commercial_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id                 UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    commercial_subtype          commercial_subtype_enum NOT NULL,
    occupancy_type              commercial_occupancy_enum NOT NULL,
    grade                       commercial_grade_enum,
    floor_number                SMALLINT,
    total_floors                SMALLINT,
    num_cabins                  SMALLINT,
    num_conference_rooms        SMALLINT,
    workstation_capacity        INTEGER,
    furnishing_status           furnishing_status_enum NOT NULL,
    lease_duration_min_months   SMALLINT,
    lease_escalation_pct        NUMERIC(5,2),
    security_deposit_months     SMALLINT,
    car_parking_slots           SMALLINT,
    has_uds                     BOOLEAN DEFAULT FALSE,
    has_datacenter_infra        BOOLEAN DEFAULT FALSE,
    power_supply_kva            NUMERIC(8,2),
    has_fire_noc                BOOLEAN DEFAULT FALSE,
    building_name               VARCHAR(150),
    developer_id                UUID REFERENCES organisations(organisation_id),
    reit_eligible               BOOLEAN DEFAULT FALSE,
    current_tenant_id           UUID REFERENCES organisations(organisation_id),
    noi_per_year                NUMERIC(15,2),
    cap_rate                    NUMERIC(6,4),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_commercial_updated_at
    BEFORE UPDATE ON commercial_properties
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 5. PLOTS
-- ============================================================
CREATE TABLE plots (
    plot_id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id             UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    plot_subtype            plot_subtype_enum NOT NULL,
    plot_area_sqft          NUMERIC(12,2) NOT NULL CHECK (plot_area_sqft > 0),
    plot_area_sqmtr         NUMERIC(12,2)
                                GENERATED ALWAYS AS (ROUND(plot_area_sqft * 0.0929, 2)) STORED,
    plot_area_guntha        NUMERIC(10,4),
    plot_area_bigha         NUMERIC(10,4),
    plot_area_acres         NUMERIC(10,4),
    boundary_polygon        geography(POLYGON, 4326),
    survey_number           VARCHAR(60),
    khata_number            VARCHAR(60),
    gat_number              VARCHAR(60),
    plot_number             VARCHAR(40),
    layout_name             VARCHAR(150),
    zone_type               zone_type_enum,
    land_use                plot_subtype_enum,
    is_na_converted         BOOLEAN DEFAULT FALSE,
    na_order_number         VARCHAR(80),
    is_dtcp_approved        BOOLEAN DEFAULT FALSE,
    is_hmda_approved        BOOLEAN DEFAULT FALSE,
    is_rera_registered      BOOLEAN DEFAULT FALSE,
    road_width_meters       NUMERIC(6,2),
    road_type               road_type_enum,
    corner_plot             BOOLEAN DEFAULT FALSE,
    fsi_available           NUMERIC(5,2),
    permissible_use         TEXT,
    electricity_connection  BOOLEAN DEFAULT FALSE,
    water_connection        BOOLEAN DEFAULT FALSE,
    fencing_type            VARCHAR(30),
    ownership_type          ownership_type_enum,
    encumbrance_free        BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_plots_updated_at
    BEFORE UPDATE ON plots
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 6. VILLAS
-- ============================================================
CREATE TABLE villas (
    villa_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id             UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    villa_subtype           villa_subtype_enum NOT NULL,
    num_bedrooms            SMALLINT NOT NULL CHECK (num_bedrooms > 0),
    num_bathrooms           SMALLINT NOT NULL CHECK (num_bathrooms > 0),
    num_floors              SMALLINT,
    plot_area_sqft          NUMERIC(10,2),
    private_garden_sqft     NUMERIC(10,2),
    private_pool            BOOLEAN DEFAULT FALSE,
    private_gym             BOOLEAN DEFAULT FALSE,
    home_theatre            BOOLEAN DEFAULT FALSE,
    smart_home_system       BOOLEAN DEFAULT FALSE,
    parking_covered         SMALLINT DEFAULT 0,
    car_porch               BOOLEAN DEFAULT FALSE,
    servant_quarters        BOOLEAN DEFAULT FALSE,
    terrace_sqft            NUMERIC(8,2),
    elevator                BOOLEAN DEFAULT FALSE,
    facing_direction        facing_direction_enum,
    is_gated_community      BOOLEAN DEFAULT FALSE,
    community_id            UUID,               -- FK to gated_communities when table exists
    has_swimming_pool       BOOLEAN DEFAULT FALSE,
    has_clubhouse           BOOLEAN DEFAULT FALSE,
    maintenance_per_sqft    NUMERIC(7,2),
    furnishing_status       furnishing_status_enum,
    possession_status       possession_status_enum NOT NULL,
    possession_date         DATE,
    age_of_property_yrs     SMALLINT,
    water_bodies            TEXT[]  DEFAULT '{}',
    amenity_ids             UUID[]  DEFAULT '{}',
    floor_plan_url          VARCHAR(500),
    virtual_tour_url        VARCHAR(500),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_villas_updated_at
    BEFORE UPDATE ON villas
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 7. WAREHOUSES
-- ============================================================
CREATE TABLE warehouses (
    warehouse_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id                 UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    warehouse_subtype           warehouse_subtype_enum NOT NULL,
    floor_height_meters         NUMERIC(5,2),
    loading_docks               SMALLINT,
    dock_levellers              BOOLEAN DEFAULT FALSE,
    floor_load_capacity_kg_sqm  NUMERIC(8,2),
    fire_suppression            fire_suppression_enum,
    power_supply_kva            NUMERIC(8,2),
    power_backup_pct            SMALLINT CHECK (power_backup_pct BETWEEN 0 AND 100),
    is_temperature_controlled   BOOLEAN DEFAULT FALSE,
    min_temperature_c           NUMERIC(5,1),
    max_temperature_c           NUMERIC(5,1),
    total_area_sqft             NUMERIC(12,2) NOT NULL CHECK (total_area_sqft > 0),
    office_area_sqft            NUMERIC(8,2),
    yard_area_sqft              NUMERIC(12,2),
    truck_bays_capacity         SMALLINT,
    nh_distance_km              NUMERIC(6,2),
    port_distance_km            NUMERIC(6,2),
    airport_distance_km         NUMERIC(6,2),
    rail_siding                 BOOLEAN DEFAULT FALSE,
    is_bonded                   BOOLEAN DEFAULT FALSE,
    gstin                       VARCHAR(15),
    occupancy_certificate       BOOLEAN DEFAULT FALSE,
    seismic_zone                seismic_zone_enum,
    flood_risk                  flood_risk_enum,
    wms_compatible              BOOLEAN DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_warehouses_updated_at
    BEFORE UPDATE ON warehouses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 8. CO-WORKING SPACES
-- ============================================================
CREATE TABLE coworking_spaces (
    coworking_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id             UUID NOT NULL UNIQUE REFERENCES properties(property_id) ON DELETE CASCADE,
    space_subtype           coworking_subtype_enum NOT NULL,
    operator_id             UUID NOT NULL REFERENCES organisations(organisation_id),
    centre_id               UUID,               -- FK to coworking_centres when table exists
    total_seats             INTEGER,
    available_seats         INTEGER,
    min_seats               INTEGER DEFAULT 1,
    pricing_model           pricing_model_enum NOT NULL,
    price_per_seat_monthly  NUMERIC(8,2),
    price_per_hour          NUMERIC(6,2),
    price_per_day           NUMERIC(7,2),
    min_commitment_months   SMALLINT DEFAULT 0,
    security_deposit_months SMALLINT,
    has_cabins              BOOLEAN DEFAULT FALSE,
    has_meeting_rooms       BOOLEAN DEFAULT FALSE,
    meeting_room_credits    INTEGER,
    has_phone_booths        BOOLEAN DEFAULT FALSE,
    internet_speed_mbps     INTEGER,
    internet_redundancy     BOOLEAN DEFAULT FALSE,
    has_cafe                BOOLEAN DEFAULT FALSE,
    has_printing            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_coworking_updated_at
    BEFORE UPDATE ON coworking_spaces
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 9. TRANSACTION PIPELINE
-- ============================================================

-- 9.1 enquiries
CREATE TABLE enquiries (
    enquiry_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    user_id             UUID REFERENCES users(user_id),
    -- Anonymous contact info (for unregistered users)
    contact_name        VARCHAR(200),
    contact_phone       VARCHAR(20),
    contact_email       VARCHAR(255),
    channel             enquiry_channel_enum NOT NULL DEFAULT 'PLATFORM_FORM',
    status              enquiry_status_enum  NOT NULL DEFAULT 'NEW',
    message             TEXT,
    budget_min          NUMERIC(15,2),
    budget_max          NUMERIC(15,2),
    intent_score        SMALLINT DEFAULT 0 CHECK (intent_score BETWEEN 0 AND 100),
    assigned_broker_id  UUID REFERENCES users(user_id),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9.2 site_visits
CREATE TABLE site_visits (
    visit_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enquiry_id          UUID NOT NULL REFERENCES enquiries(enquiry_id),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    user_id             UUID REFERENCES users(user_id),
    broker_id           UUID REFERENCES users(user_id),
    scheduled_at        TIMESTAMPTZ NOT NULL,
    completed_at        TIMESTAMPTZ,
    status              VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    visitor_feedback    TEXT,
    rating              SMALLINT CHECK (rating BETWEEN 1 AND 5),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9.3 offers
CREATE TABLE offers (
    offer_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    enquiry_id          UUID REFERENCES enquiries(enquiry_id),
    buyer_id            UUID NOT NULL REFERENCES users(user_id),
    offered_price       NUMERIC(15,2) NOT NULL CHECK (offered_price > 0),
    status              offer_status_enum NOT NULL DEFAULT 'SUBMITTED',
    validity_date       TIMESTAMPTZ,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9.4 agreements
CREATE TABLE agreements (
    agreement_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    offer_id            UUID NOT NULL REFERENCES offers(offer_id),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    buyer_id            UUID NOT NULL REFERENCES users(user_id),
    seller_id           UUID NOT NULL REFERENCES users(user_id),
    agreement_type      agreement_type_enum   NOT NULL,
    status              agreement_status_enum NOT NULL DEFAULT 'DRAFT',
    agreed_price        NUMERIC(15,2) NOT NULL,
    stamp_duty_paid     NUMERIC(12,2),
    registration_date   DATE,
    document_url        VARCHAR(500),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 10. ANALYTICS & AI TABLES
-- ============================================================

-- 10.1 property_price_history (append-only ledger, partitioned)
CREATE TABLE property_price_history (
    history_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    event_type          price_event_type_enum NOT NULL,
    price               NUMERIC(15,2) NOT NULL,
    price_per_sqft      NUMERIC(10,2),
    source              data_source_enum NOT NULL,
    recorded_by_user_id UUID REFERENCES users(user_id),
    notes               TEXT,
    event_date          DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10.2 avm_valuations (append-only, one record per model run)
CREATE TABLE avm_valuations (
    valuation_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id         UUID NOT NULL REFERENCES properties(property_id),
    estimated_value     NUMERIC(15,2) NOT NULL,
    low_estimate        NUMERIC(15,2) NOT NULL,
    high_estimate       NUMERIC(15,2) NOT NULL,
    confidence_score    NUMERIC(4,3)  NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    model_version       VARCHAR(20)   NOT NULL,
    comparables_used    JSONB,
    data_quality        data_quality_enum NOT NULL,
    valuation_date      DATE          NOT NULL DEFAULT CURRENT_DATE,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- 10.3 neighbourhood_scores
CREATE TABLE neighbourhood_scores (
    score_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    locality            VARCHAR(120) NOT NULL,
    city                VARCHAR(80)  NOT NULL,
    overall_score       NUMERIC(5,2) NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    connectivity_score  NUMERIC(5,2) NOT NULL,
    school_score        NUMERIC(5,2) NOT NULL,
    hospital_score      NUMERIC(5,2) NOT NULL,
    green_score         NUMERIC(5,2) NOT NULL,
    safety_score        NUMERIC(5,2) NOT NULL,
    price_trend_1yr     NUMERIC(6,3),
    price_trend_3yr     NUMERIC(6,3),
    rental_yield_pct    NUMERIC(5,2),
    demand_index        NUMERIC(6,2),
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 11. MEDIA ASSETS
-- ============================================================
CREATE TABLE media_assets (
    asset_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id         UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
    asset_type          VARCHAR(30) NOT NULL,   -- IMAGE|VIDEO|FLOOR_PLAN|VIRTUAL_TOUR|DOCUMENT
    url                 VARCHAR(1000) NOT NULL,
    thumbnail_url       VARCHAR(1000),
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    sequence_order      SMALLINT DEFAULT 0,
    ai_tags             JSONB   DEFAULT '[]',
    ai_quality_score    NUMERIC(3,2) CHECK (ai_quality_score BETWEEN 0 AND 1),
    uploaded_by         UUID REFERENCES users(user_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 12. INDEXES
-- ============================================================

-- properties base table
CREATE INDEX idx_prop_type_status_city     ON properties (property_type, listing_status, listing_status);
CREATE INDEX idx_prop_location             ON properties (location_id);
CREATE INDEX idx_prop_price                ON properties (asking_price);
CREATE INDEX idx_prop_price_psf            ON properties (price_per_sqft);
CREATE INDEX idx_prop_active               ON properties (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_prop_posted_active        ON properties (posted_at DESC) WHERE is_active = TRUE;
CREATE INDEX idx_prop_featured             ON properties (is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_prop_tenant               ON properties (platform_tenant_id);
CREATE INDEX idx_prop_rera                 ON properties (rera_id);
CREATE INDEX idx_prop_poster               ON properties (posted_by_user_id);
CREATE INDEX idx_prop_geo                  ON properties USING GIST (geo_point);
CREATE INDEX idx_prop_tags                 ON properties USING GIN  (tags);
CREATE INDEX idx_prop_attrs                ON properties USING GIN  (attributes);
CREATE INDEX idx_prop_fts                  ON properties USING GIN  (
    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,''))
);
-- HNSW index for semantic vector search (requires pgvector >= 0.5)
CREATE INDEX idx_prop_vector_hnsw          ON properties USING hnsw (description_vector vector_cosine_ops);

-- locations
CREATE INDEX idx_loc_city                  ON locations (city);
CREATE INDEX idx_loc_locality              ON locations (locality);
CREATE INDEX idx_loc_pin                   ON locations (pin_code);
CREATE INDEX idx_loc_state                 ON locations (state_code);
CREATE INDEX idx_loc_survey                ON locations (survey_number, state_code);
CREATE INDEX idx_loc_geo                   ON locations USING GIST (geo_point);
CREATE INDEX idx_loc_polygon               ON locations USING GIST (geo_polygon);

-- residential
CREATE INDEX idx_res_prop                  ON residential_properties (property_id);
CREATE INDEX idx_res_bhk_poss              ON residential_properties (bhk_type, possession_status);
CREATE INDEX idx_res_vastu                 ON residential_properties (is_vastu_compliant);
CREATE INDEX idx_res_floor                 ON residential_properties (floor_number);
CREATE INDEX idx_res_amenities             ON residential_properties USING GIN (amenity_ids);

-- commercial
CREATE INDEX idx_com_prop                  ON commercial_properties (property_id);
CREATE INDEX idx_com_grade_occ             ON commercial_properties (grade, occupancy_type);
CREATE INDEX idx_com_workstations          ON commercial_properties (workstation_capacity);

-- plots
CREATE INDEX idx_plot_prop                 ON plots (property_id);
CREATE INDEX idx_plot_subtype              ON plots (plot_subtype);
CREATE INDEX idx_plot_survey               ON plots (survey_number);
CREATE INDEX idx_plot_khata                ON plots (khata_number);
CREATE INDEX idx_plot_area                 ON plots (plot_area_sqft);
CREATE INDEX idx_plot_boundary             ON plots USING GIST (boundary_polygon);

-- villas
CREATE INDEX idx_villa_prop                ON villas (property_id);
CREATE INDEX idx_villa_gated               ON villas (is_gated_community);
CREATE INDEX idx_villa_pool                ON villas (private_pool);
CREATE INDEX idx_villa_poss                ON villas (possession_status);

-- warehouses
CREATE INDEX idx_wh_prop                   ON warehouses (property_id);
CREATE INDEX idx_wh_subtype_height         ON warehouses (warehouse_subtype, floor_height_meters);
CREATE INDEX idx_wh_area                   ON warehouses (total_area_sqft);
CREATE INDEX idx_wh_nh_dist                ON warehouses (nh_distance_km);

-- coworking
CREATE INDEX idx_cw_prop                   ON coworking_spaces (property_id);
CREATE INDEX idx_cw_operator               ON coworking_spaces (operator_id);
CREATE INDEX idx_cw_price_seats            ON coworking_spaces (price_per_seat_monthly, available_seats);

-- enquiries
CREATE INDEX idx_enq_property_status       ON enquiries (property_id, status, created_at);
CREATE INDEX idx_enq_user                  ON enquiries (user_id);
CREATE INDEX idx_enq_broker                ON enquiries (assigned_broker_id);
CREATE INDEX idx_enq_intent                ON enquiries (intent_score DESC);

-- price history
CREATE INDEX idx_ph_prop_date              ON property_price_history (property_id, event_date DESC);

-- avm valuations
CREATE INDEX idx_avm_prop_date             ON avm_valuations (property_id, valuation_date DESC);
CREATE INDEX idx_avm_confidence            ON avm_valuations (confidence_score);

-- neighbourhood scores
CREATE INDEX idx_nbhd_city_locality        ON neighbourhood_scores (city, locality);
CREATE INDEX idx_nbhd_computed             ON neighbourhood_scores (computed_at DESC);
CREATE INDEX idx_nbhd_overall              ON neighbourhood_scores (overall_score DESC);

-- media assets
CREATE INDEX idx_media_prop                ON media_assets (property_id);
CREATE INDEX idx_media_primary             ON media_assets (property_id) WHERE is_primary = TRUE;

-- offers / agreements
CREATE INDEX idx_offer_prop                ON offers (property_id, status);
CREATE INDEX idx_offer_buyer               ON offers (buyer_id);
CREATE INDEX idx_agree_prop                ON agreements (property_id);

-- rera
CREATE INDEX idx_rera_number               ON rera_registrations (rera_number);
CREATE INDEX idx_rera_state_status         ON rera_registrations (state_code, status);
CREATE INDEX idx_rera_promoter             ON rera_registrations (promoter_id);

-- ============================================================
-- 13. ROW-LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE properties        ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiries         ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers            ENABLE ROW LEVEL SECURITY;
ALTER TABLE agreements        ENABLE ROW LEVEL SECURITY;

-- Admins/service role bypass all RLS
CREATE POLICY rls_properties_service ON properties
    USING (current_user = 'realty_service');

CREATE POLICY rls_properties_owner ON properties
    USING (posted_by_user_id::text = current_setting('app.current_user_id', TRUE));

CREATE POLICY rls_enquiries_broker ON enquiries
    USING (
        assigned_broker_id::text = current_setting('app.current_user_id', TRUE)
        OR user_id::text          = current_setting('app.current_user_id', TRUE)
    );

-- ============================================================
-- 14. HELPFUL VIEWS
-- ============================================================

-- Active residential listings with location joined
CREATE OR REPLACE VIEW v_active_residential AS
SELECT
    p.property_id,
    p.title,
    p.listing_status,
    p.transaction_type,
    p.asking_price,
    p.price_per_sqft,
    p.carpet_area_sqft,
    p.is_verified,
    p.is_featured,
    p.views_count,
    p.enquiry_count,
    p.posted_at,
    r.bhk_type,
    r.num_bedrooms,
    r.num_bathrooms,
    r.floor_number,
    r.total_floors,
    r.furnishing_status,
    r.possession_status,
    r.possession_date,
    r.is_vastu_compliant,
    r.parking_covered,
    l.locality,
    l.city,
    l.state_code,
    l.pin_code,
    l.latitude,
    l.longitude
FROM properties p
JOIN residential_properties r ON r.property_id = p.property_id
JOIN locations              l ON l.location_id  = p.location_id
WHERE p.is_active = TRUE
  AND p.listing_status = 'ACTIVE'
  AND p.deleted_at IS NULL;

-- Latest AVM valuation per property
CREATE OR REPLACE VIEW v_latest_avm AS
SELECT DISTINCT ON (property_id)
    property_id,
    estimated_value,
    low_estimate,
    high_estimate,
    confidence_score,
    model_version,
    valuation_date
FROM avm_valuations
ORDER BY property_id, valuation_date DESC;

-- Latest neighbourhood score per locality
CREATE OR REPLACE VIEW v_latest_neighbourhood_score AS
SELECT DISTINCT ON (city, locality)
    city,
    locality,
    overall_score,
    connectivity_score,
    school_score,
    hospital_score,
    safety_score,
    rental_yield_pct,
    demand_index,
    computed_at
FROM neighbourhood_scores
ORDER BY city, locality, computed_at DESC;

-- ============================================================
-- 15. GRANT PERMISSIONS (adjust roles to your setup)
-- ============================================================

-- GRANT USAGE ON SCHEMA realty_os TO realty_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA realty_os TO realty_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA realty_os TO realty_app;
-- GRANT SELECT ON ALL TABLES IN SCHEMA realty_os TO realty_readonly;

-- ============================================================
-- END OF MIGRATION
-- ============================================================