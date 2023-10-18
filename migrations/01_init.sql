CREATE TABLE IF NOT EXISTS general_cities (
	id SERIAL PRIMARY KEY,
	value TEXT
);

-- male
CREATE TABLE IF NOT EXISTS general_names_male (
	id SERIAL PRIMARY KEY,
	value TEXT
);

-- female
CREATE TABLE IF NOT EXISTS general_names_female (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS general_surnames (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS general_countries (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_invalid (
	id SERIAL PRIMARY KEY,
	name TEXT,
	value TEXT
);
CREATE INDEX IF NOT EXISTS creative_invalid_name_idx ON creative_invalid(name);

CREATE TABLE IF NOT EXISTS creative_unchecked (
	id SERIAL PRIMARY KEY,
	name TEXT,
	value TEXT
);
CREATE INDEX IF NOT EXISTS creative_unchecked_name_idx ON creative_unchecked(name);

CREATE TABLE IF NOT EXISTS creative_unchecked_actual_invalid (
  id SERIAL PRIMARY KEY,
  name TEXT,
  unchecked_id INTEGER,
  actual_id INTEGER,
  invalid_id INTEGER
);
CREATE INDEX IF NOT EXISTS creative_unchecked_actual_invalid_name_actual_id_idx ON creative_unchecked_actual_invalid(name, actual_id);
CREATE INDEX IF NOT EXISTS creative_unchecked_actual_invalid_name_invalid_id_idx ON creative_unchecked_actual_invalid(name, invalid_id);

CREATE TABLE IF NOT EXISTS creative_awkward_moment (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_bookname (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_character (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_crowd (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_features (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_jobs (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_motivation (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_plot (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_race (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_superpowers (
	id SERIAL PRIMARY KEY,
  title TEXT,
	description TEXT
);

CREATE TABLE IF NOT EXISTS creative_unexpected_event (
	id SERIAL PRIMARY KEY,
	value TEXT
);

CREATE TABLE IF NOT EXISTS creative_wp (
  id SERIAL PRIMARY KEY,
  value TEXT,
  english TEXT
);

CREATE TABLE IF NOT EXISTS creative_wp_invalid (
  id SERIAL PRIMARY KEY,
  value TEXT,
  english TEXT
);

CREATE TABLE IF NOT EXISTS creative_wp_unchecked (
  id SERIAL PRIMARY KEY,
  value TEXT,
  english TEXT
);

CREATE TABLE IF NOT EXISTS creative_wp_unchecked_actual_invalid (
  id SERIAL PRIMARY KEY,
  unchecked_id INTEGER,
  actual_id INTEGER,
  invalid_id INTEGER
);

CREATE TABLE IF NOT EXISTS general_info (
	id SERIAL PRIMARY KEY,
	category TEXT,
	position INTEGER,
	name TEXT,
	title TEXT,
	description_mainpage TEXT,
	description_generator TEXT,
	meta_description TEXT,
	meta_keywords TEXT,
	usergen BOOLEAN
);


CREATE TABLE IF NOT EXISTS auth_user (
	id SERIAL PRIMARY KEY,
	username TEXT,
	email TEXT,
	password TEXT,
	active BOOLEAN,
	verified BOOLEAN,

	created_at TIMESTAMP WITH TIME ZONE,
	last_login TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS auth_user_username_idx ON auth_user(username);
CREATE INDEX IF NOT EXISTS auth_user_email_idx ON auth_user(email);

CREATE TABLE IF NOT EXISTS auth_role (
	id SERIAL PRIMARY KEY,
	name TEXT
);
CREATE INDEX IF NOT EXISTS auth_role_name_idx ON auth_role(name);

CREATE TABLE IF NOT EXISTS auth_permission (
  id SERIAL PRIMARY KEY,
  name TEXT
);
CREATE INDEX IF NOT EXISTS auth_permission_name_idx ON auth_permission(name);

CREATE TABLE IF NOT EXISTS auth_user_role (
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
	role_id INTEGER REFERENCES auth_role(id) ON DELETE CASCADE,
	PRIMARY KEY(user_id, role_id)
);
CREATE INDEX IF NOT EXISTS auth_user_role_user_id_idx ON auth_user_role(user_id);
CREATE INDEX IF NOT EXISTS auth_user_role_role_id_idx ON auth_user_role(role_id);

CREATE TABLE IF NOT EXISTS auth_role_permission (
  role_id INTEGER REFERENCES auth_role(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES auth_permission(id) ON DELETE CASCADE,
	PRIMARY KEY(role_id, permission_id)
);
CREATE INDEX IF NOT EXISTS auth_role_permission_role_id_idx ON auth_role_permission(role_id);
CREATE INDEX IF NOT EXISTS auth_role_permission_permission_id_idx ON auth_role_permission(permission_id);

CREATE TABLE IF NOT EXISTS auth_oauth (
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
	provider TEXT,
	sid TEXT,
  PRIMARY KEY(user_id)
);
CREATE INDEX IF NOT EXISTS auth_oauth_provider_sid_idx ON auth_oauth(provider, sid);

CREATE TABLE IF NOT EXISTS copyrighter (
	id SERIAL PRIMARY KEY,
	name TEXT,
	url TEXT
);

CREATE TABLE IF NOT EXISTS category (
	id SERIAL PRIMARY KEY,
	name TEXT
);
CREATE INDEX IF NOT EXISTS category_name_idx ON category(name);

CREATE TABLE IF NOT EXISTS generator (
  id SERIAL PRIMARY KEY,
  name TEXT
);

CREATE TABLE IF NOT EXISTS feature (
  id SERIAL PRIMARY KEY,
  generator_id INTEGER REFERENCES generator(id),
  name TEXT
);
CREATE INDEX IF NOT EXISTS feature_name_idx ON feature(name);

CREATE TABLE IF NOT EXISTS gen (
	id SERIAL PRIMARY KEY,
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,

	title TEXT,
	description TEXT,

	access INTEGER,

	category_id INTEGER REFERENCES category(id),
	-- subcategories
	-- tags

  generator_id INTEGER REFERENCES generator(id),
  -- engine_generator_feature

	format JSONB,
	body JSONB,

	-- likes
	-- likes_count
	-- favs
	-- favs_count
	views BIGINT DEFAULT 0,

	date_added TIMESTAMP WITH TIME ZONE,
	date_updated TIMESTAMP WITH TIME ZONE,

	access_key TEXT,
	hash TEXT,
	variations BIGINT,

	active BOOLEAN DEFAULT TRUE,
	ads BOOLEAN DEFAULT TRUE,

	copyright BOOLEAN DEFAULT FALSE,
	copyrighter_id INTEGER REFERENCES copyrighter(id)
);


CREATE TABLE IF NOT EXISTS gen_feature (
  gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
  feature_id INTEGER REFERENCES feature(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_id, feature_id)
);

CREATE TABLE IF NOT EXISTS global_setting (
  id SERIAL PRIMARY KEY,
  section TEXT,
  name TEXT,
  i_value INTEGER,
  s_value TEXT,
  b_value BOOLEAN
);
CREATE INDEX IF NOT EXISTS global_setting_section_name_idx ON global_setting(section, name);

CREATE TABLE IF NOT EXISTS gen_like (
	gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_id, user_id)
);

CREATE TABLE IF NOT EXISTS gen_fav (
  id BIGSERIAL PRIMARY KEY,
	gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
  added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS gen_fav_gen_id_user_id_idx ON gen_fav(gen_id, user_id);

CREATE TABLE IF NOT EXISTS subcategory (
	id SERIAL PRIMARY KEY,
	category_id INTEGER REFERENCES category(id),
	name TEXT
);

CREATE TABLE IF NOT EXISTS gen_subcategory (
	gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
	subcategory_id INTEGER REFERENCES subcategory(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_id, subcategory_id)
);

CREATE TABLE IF NOT EXISTS tag (
	id SERIAL PRIMARY KEY,
	name TEXT
);

CREATE TABLE IF NOT EXISTS gen_tag (
	gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
	tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_id, tag_id)
);

/* VH */

CREATE TABLE IF NOT EXISTS gen_vh (
  id SERIAL PRIMARY KEY,

  gen_id INTEGER REFERENCES gen(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,

  title TEXT,
  description TEXT,

  access INTEGER,

	category_id INTEGER REFERENCES category(id),
	-- subcategories
	-- tags

  generator_id INTEGER REFERENCES generator(id),
  -- engine_generator_feature

	format JSONB,
	body JSONB,

	created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS gen_vh_feature (
  gen_vh_id INTEGER REFERENCES gen_vh(id) ON DELETE CASCADE,
  feature_id INTEGER REFERENCES feature(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_vh_id, feature_id)
);

CREATE TABLE IF NOT EXISTS gen_vh_subcategory (
	gen_vh_id INTEGER REFERENCES gen_vh(id) ON DELETE CASCADE,
	subcategory_id INTEGER REFERENCES subcategory(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_vh_id, subcategory_id)
);

CREATE TABLE IF NOT EXISTS gen_vh_tag (
	gen_vh_id INTEGER REFERENCES gen_vh(id) ON DELETE CASCADE,
	tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,
  PRIMARY KEY(gen_vh_id, tag_id)
);

/* LIST */

CREATE TABLE IF NOT EXISTS list (
	id SERIAL PRIMARY KEY,
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,

	title TEXT,
	description TEXT,
	access INTEGER,

	content TEXT,
	slicer INTEGER,

	active BOOLEAN,

	date_added TIMESTAMP WITH TIME ZONE,
	date_updated TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS list_user_id_idx ON list(user_id);

CREATE TABLE IF NOT EXISTS user_event (
  id BIGSERIAL PRIMARY KEY,
  name TEXT,
  user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
  data JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profile_notification (
	id SERIAL PRIMARY KEY,
	user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
	message TEXT,
	created_at TIMESTAMP WITH TIME ZONE,
	seen BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS profile_info (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
  description TEXT DEFAULT NULL
);
