BEGIN;
DELETE FROM "public"."django_migrations" WHERE "id" = 3;
DELETE FROM "public"."django_migrations" WHERE "id" = 5;
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'default', '0001_initial', '2018-02-15 11:10:39.481267+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_auth', '0001_initial', '2018-02-15 11:10:39.48374+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'default', '0002_add_related_name', '2018-02-15 11:10:39.505145+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_auth', '0002_add_related_name', '2018-02-15 11:10:39.508373+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'default', '0003_alter_email_max_length', '2018-02-15 11:10:39.517832+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_auth', '0003_alter_email_max_length', '2018-02-15 11:10:39.520148+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'default', '0004_auto_20160423_0400', '2018-02-15 11:10:39.536098+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_auth', '0004_auto_20160423_0400', '2018-02-15 11:10:39.539983+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_auth', '0005_auto_20160727_2333', '2018-02-15 11:10:39.55099+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0001_initial', '2018-02-15 11:10:39.558089+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0003_alter_email_max_length', '2018-02-15 11:10:39.560909+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0002_add_related_name', '2018-02-15 11:10:39.563989+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0004_auto_20160423_0400', '2018-02-15 11:10:39.566734+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0005_auto_20160727_2333', '2018-02-15 11:10:39.569399+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0006_partial', '2018-02-15 11:11:24.699972+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0007_code_timestamp', '2018-02-15 11:11:24.717516+00');
INSERT INTO "public"."django_migrations" VALUES (nextval('django_migrations_id_seq'), 'social_django', '0008_partial_timestamp', '2018-02-15 11:11:24.737398+00');
COMMIT;

CREATE SEQUENCE social_auth_code_id_seq;
-- ----------------------------
-- Table structure for social_auth_code
-- ----------------------------
DROP TABLE IF EXISTS "public"."social_auth_code";
CREATE TABLE "public"."social_auth_code" (
  "id" int4 NOT NULL DEFAULT nextval('social_auth_code_id_seq'::regclass),
  "email" varchar(254) COLLATE "pg_catalog"."default" NOT NULL,
  "code" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "verified" bool NOT NULL,
  "timestamp" timestamptz(6) NOT NULL
)
;
ALTER TABLE "public"."social_auth_code" OWNER TO "djangopackages";

-- ----------------------------
-- Indexes structure for table social_auth_code
-- ----------------------------
CREATE INDEX "social_auth_code_code_a2393167" ON "public"."social_auth_code" USING btree (
  "code" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "social_auth_code_code_a2393167_like" ON "public"."social_auth_code" USING btree (
  "code" COLLATE "pg_catalog"."default" "pg_catalog"."varchar_pattern_ops" ASC NULLS LAST
);
CREATE INDEX "social_auth_code_timestamp_176b341f" ON "public"."social_auth_code" USING btree (
  "timestamp" "pg_catalog"."timestamptz_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table social_auth_code
-- ----------------------------
ALTER TABLE "public"."social_auth_code" ADD CONSTRAINT "social_auth_code_email_code_801b2d02_uniq" UNIQUE ("email", "code");

-- ----------------------------
-- Primary Key structure for table social_auth_code
-- ----------------------------
ALTER TABLE "public"."social_auth_code" ADD CONSTRAINT "social_auth_code_pkey" PRIMARY KEY ("id");

CREATE SEQUENCE social_auth_partial_id_seq;
-- ----------------------------
-- Table structure for social_auth_partial
-- ----------------------------
DROP TABLE IF EXISTS "public"."social_auth_partial";
CREATE TABLE "public"."social_auth_partial" (
  "id" int4 NOT NULL DEFAULT nextval('social_auth_partial_id_seq'::regclass),
  "token" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "next_step" int2 NOT NULL,
  "backend" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "data" text COLLATE "pg_catalog"."default" NOT NULL,
  "timestamp" timestamptz(6) NOT NULL
)
;
ALTER TABLE "public"."social_auth_partial" OWNER TO "djangopackages";

-- ----------------------------
-- Indexes structure for table social_auth_partial
-- ----------------------------
CREATE INDEX "social_auth_partial_timestamp_50f2119f" ON "public"."social_auth_partial" USING btree (
  "timestamp" "pg_catalog"."timestamptz_ops" ASC NULLS LAST
);
CREATE INDEX "social_auth_partial_token_3017fea3" ON "public"."social_auth_partial" USING btree (
  "token" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX "social_auth_partial_token_3017fea3_like" ON "public"."social_auth_partial" USING btree (
  "token" COLLATE "pg_catalog"."default" "pg_catalog"."varchar_pattern_ops" ASC NULLS LAST
);

-- ----------------------------
-- Checks structure for table social_auth_partial
-- ----------------------------
ALTER TABLE "public"."social_auth_partial" ADD CONSTRAINT "social_auth_partial_next_step_check" CHECK ((next_step >= 0));

-- ----------------------------
-- Primary Key structure for table social_auth_partial
-- ----------------------------
ALTER TABLE "public"."social_auth_partial" ADD CONSTRAINT "social_auth_partial_pkey" PRIMARY KEY ("id");
