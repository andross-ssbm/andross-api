CREATE TABLE IF NOT EXISTS entry_date (
    entry_time TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS character_list (
    id integer PRIMARY KEY,
    name character varying(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id bigint PRIMARY KEY,
    cc character varying(10) NOT NULL,
    name character varying(14) NOT NULL,
    main_id integer DEFAULT 256,
    slippi_id character varying(64) DEFAULT '0' NOT NULL,
    latest_elo double precision DEFAULT '1100'::double precision NOT NULL,
    latest_wins integer DEFAULT 0 NOT NULL,
    latest_losses integer DEFAULT 0 NOT NULL,
    latest_dgp integer DEFAULT 0 NOT NULL,
    latest_drp integer DEFAULT 0 NOT NULL,
    is_michigan boolean DEFAULT true NOT NULL,
    FOREIGN KEY(main_id) REFERENCES character_list(id)
);

CREATE TABLE IF NOT EXISTS elo (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    elo double precision DEFAULT '0'::double precision NOT NULL,
    entry_time timestamp WITHOUT TIME ZONE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE OR REPLACE FUNCTION update_latest_elo()
RETURNS TRIGGER AS $$
BEGIN
UPDATE users SET latest_elo = NEW.elo WHERE users.id = NEW.user_id;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_latest_elo_trigger
AFTER INSERT OR UPDATE ON elo
FOR EACH ROW
EXECUTE FUNCTION update_latest_elo();

CREATE TABLE IF NOT EXISTS win_loss (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    wins integer DEFAULT 0 NOT NULL,
    losses integer DEFAULT 0 NOT NULL,
    entry_time timestamp WITHOUT TIME ZONE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE OR REPLACE FUNCTION update_latest_win_loss()
RETURNS TRIGGER AS $$
BEGIN
UPDATE users SET latest_wins = NEW.wins WHERE users.id = NEW.user_id;
UPDATE users SET latest_losses = NEW.losses WHERE users.id = NEW.user_id;
RETURN NEW;
                END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_latest_win_loss_trigger
AFTER INSERT OR UPDATE ON win_loss
FOR EACH ROW
EXECUTE FUNCTION update_latest_win_loss();

CREATE TABLE IF NOT EXISTS daily_global_placement (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    placement integer DEFAULT 0 NOT NULL,
    entry_time timestamp WITHOUT TIME ZONE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE OR REPLACE FUNCTION update_latest_dgp()
RETURNS TRIGGER AS $$
BEGIN
UPDATE users SET latest_dgp = NEW.placement WHERE users.id = NEW.user_id;
RETURN NEW;
                END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_latest_dgp_trigger
AFTER INSERT OR UPDATE ON daily_global_placement
FOR EACH ROW
EXECUTE FUNCTION update_latest_dgp();

CREATE TABLE IF NOT EXISTS daily_regional_placement (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    placement integer DEFAULT 0 NOT NULL,
    entry_time timestamp WITHOUT TIME ZONE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE OR REPLACE FUNCTION update_latest_drp()
RETURNS TRIGGER AS $$
BEGIN
UPDATE users SET latest_drp = NEW.placement WHERE users.id = NEW.user_id;
RETURN NEW;
                END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_latest_drp_trigger
AFTER INSERT OR UPDATE ON daily_regional_placement
FOR EACH ROW
EXECUTE FUNCTION update_latest_drp();

CREATE TABLE IF NOT EXISTS character_entry (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    character_id integer NOT NULL,
    game_count integer NOT NULL,
    entry_time timestamp without time zone NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(character_id) REFERENCES character_list(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE TABLE IF NOT EXISTS leaderboard (
    id SERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    position integer DEFAULT 0 NOT NULL,
    elo double precision DEFAULT '0'::double precision NOT NULL,
    wins integer DEFAULT 0 NOT NULL,
    losses integer DEFAULT 0 NOT NULL,
    drp integer DEFAULT 0 NOT NULL,
    dgp integer DEFAULT 0 NOT NULL,
    entry_time timestamp without time zone NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(entry_time) REFERENCES entry_date(entry_time)
);

CREATE TABLE IF NOT EXISTS seasons (
    id SERIAL PRIMARY KEY,
    start_date timestamp WITHOUT TIME ZONE NOT NULL,
    end_date timestamp WITHOUT TIME ZONE,
    is_current boolean
);

CREATE OR REPLACE FUNCTION update_other_seasons()
RETURNS TRIGGER AS $$
BEGIN
IF NEW.is_current = true THEN
UPDATE seasons
SET is_current = false
WHERE is_current = true
AND id <> NEW.id;
                  END IF;

RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_seasons_trigger
AFTER INSERT ON seasons
FOR EACH ROW
EXECUTE FUNCTION update_other_seasons();

INSERT INTO character_list(id,name) VALUES (0,'DONKEY_KONG');
INSERT INTO character_list(id,name) VALUES (1,'CAPTAIN_FALCON');
INSERT INTO character_list(id,name) VALUES (2,'FOX');
INSERT INTO character_list(id,name) VALUES (3,'GAME_AND_WATCH');
INSERT INTO character_list(id,name) VALUES (4,'KIRBY');
INSERT INTO character_list(id,name) VALUES (5,'BOWSER');
INSERT INTO character_list(id,name) VALUES (6,'LINK');
INSERT INTO character_list(id,name) VALUES (7,'LUIGI');
INSERT INTO character_list(id,name) VALUES (8,'MARIO');
INSERT INTO character_list(id,name) VALUES (9,'MARTH');
INSERT INTO character_list(id,name) VALUES (10,'MEWTWO');
INSERT INTO character_list(id,name) VALUES (11,'NESS');
INSERT INTO character_list(id,name) VALUES (12,'PEACH');
INSERT INTO character_list(id,name) VALUES (13,'PIKACHU');
INSERT INTO character_list(id,name) VALUES (14,'ICE_CLIMBERS');
INSERT INTO character_list(id,name) VALUES (15,'JIGGLYPUFF');
INSERT INTO character_list(id,name) VALUES (16,'SAMUS');
INSERT INTO character_list(id,name) VALUES (17,'YOSHI');
INSERT INTO character_list(id,name) VALUES (18,'ZELDA');
INSERT INTO character_list(id,name) VALUES (19,'SHEIK');
INSERT INTO character_list(id,name) VALUES (20,'FALCO');
INSERT INTO character_list(id,name) VALUES (21,'YOUNG_LINK');
INSERT INTO character_list(id,name) VALUES (22,'DR_MARIO');
INSERT INTO character_list(id,name) VALUES (23,'ROY');
INSERT INTO character_list(id,name) VALUES (24,'PICHU');
INSERT INTO character_list(id,name) VALUES (25,'GANONDORF');
INSERT INTO character_list(id,name) VALUES (256,'None');
