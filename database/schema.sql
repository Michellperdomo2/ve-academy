BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 90c1187fc692

CREATE TABLE badges (
    id SERIAL NOT NULL, 
    code VARCHAR(60) NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    description VARCHAR(255) NOT NULL, 
    icon VARCHAR(16) NOT NULL, 
    criteria_type VARCHAR(40) NOT NULL, 
    criteria_value INTEGER NOT NULL, 
    criteria_skill VARCHAR(40), 
    points_bonus INTEGER DEFAULT '0' NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_badges PRIMARY KEY (id), 
    CONSTRAINT ck_badges_criteria_positive CHECK (criteria_value > 0), 
    CONSTRAINT uq_badges_code UNIQUE (code), 
    CONSTRAINT ck_badges_badge_criteria CHECK (criteria_type IN ('readings_completed', 'activities_completed', 'perfect_scores', 'total_points', 'skill_correct_answers')), 
    CONSTRAINT ck_badges_skill CHECK (criteria_skill IN ('phonological_awareness', 'word_recognition', 'vocabulary', 'sentence_building', 'sequencing', 'literal', 'inferential', 'critical'))
);

CREATE TABLE categories (
    id SERIAL NOT NULL, 
    name VARCHAR(60) NOT NULL, 
    slug VARCHAR(60) NOT NULL, 
    description VARCHAR(255), 
    icon VARCHAR(16), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_categories PRIMARY KEY (id), 
    CONSTRAINT uq_categories_name UNIQUE (name), 
    CONSTRAINT uq_categories_slug UNIQUE (slug)
);

CREATE TABLE challenges (
    id SERIAL NOT NULL, 
    title VARCHAR(100) NOT NULL, 
    description VARCHAR(255) NOT NULL, 
    icon VARCHAR(16) NOT NULL, 
    challenge_type VARCHAR(40) NOT NULL, 
    target INTEGER NOT NULL, 
    skill VARCHAR(40), 
    points_reward INTEGER NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_challenges PRIMARY KEY (id), 
    CONSTRAINT ck_challenges_target_positive CHECK (target > 0), 
    CONSTRAINT ck_challenges_challenge_type CHECK (challenge_type IN ('complete_readings', 'complete_activities', 'perfect_scores', 'skill_practice')), 
    CONSTRAINT ck_challenges_skill CHECK (skill IN ('phonological_awareness', 'word_recognition', 'vocabulary', 'sentence_building', 'sequencing', 'literal', 'inferential', 'critical'))
);

CREATE TABLE levels (
    id SERIAL NOT NULL, 
    number SMALLINT NOT NULL, 
    name VARCHAR(60) NOT NULL, 
    min_points INTEGER NOT NULL, 
    icon VARCHAR(16) NOT NULL, 
    CONSTRAINT pk_levels PRIMARY KEY (id), 
    CONSTRAINT uq_levels_min_points UNIQUE (min_points), 
    CONSTRAINT uq_levels_number UNIQUE (number)
);

CREATE TABLE rewards (
    id SERIAL NOT NULL, 
    code VARCHAR(40) NOT NULL, 
    name VARCHAR(60) NOT NULL, 
    kind VARCHAR(40) NOT NULL, 
    icon VARCHAR(16) NOT NULL, 
    required_level SMALLINT NOT NULL, 
    CONSTRAINT pk_rewards PRIMARY KEY (id), 
    CONSTRAINT uq_rewards_code UNIQUE (code), 
    CONSTRAINT ck_rewards_reward_kind CHECK (kind IN ('avatar', 'sticker'))
);

CREATE TABLE roles (
    id SERIAL NOT NULL, 
    code VARCHAR(40) NOT NULL, 
    name VARCHAR(60) NOT NULL, 
    description VARCHAR(255), 
    CONSTRAINT pk_roles PRIMARY KEY (id), 
    CONSTRAINT uq_roles_code UNIQUE (code), 
    CONSTRAINT ck_roles_role_code CHECK (code IN ('admin', 'teacher', 'guardian', 'student'))
);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    username VARCHAR(40) NOT NULL, 
    email VARCHAR(255), 
    password_hash VARCHAR(255) NOT NULL, 
    full_name VARCHAR(120) NOT NULL, 
    role_id INTEGER NOT NULL, 
    is_active BOOLEAN DEFAULT 'true' NOT NULL, 
    failed_login_attempts INTEGER DEFAULT '0' NOT NULL, 
    locked_until TIMESTAMP WITH TIME ZONE, 
    last_login_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_users PRIMARY KEY (id), 
    CONSTRAINT fk_users_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX ix_users_role_id ON users (role_id);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE classrooms (
    id SERIAL NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    grade VARCHAR(20) DEFAULT 'Primero' NOT NULL, 
    school_year SMALLINT NOT NULL, 
    institution VARCHAR(150), 
    teacher_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_classrooms PRIMARY KEY (id), 
    CONSTRAINT fk_classrooms_teacher_id_users FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE RESTRICT, 
    CONSTRAINT uq_classroom_teacher_name_year UNIQUE (teacher_id, name, school_year)
);

CREATE INDEX ix_classrooms_teacher_id ON classrooms (teacher_id);

CREATE TABLE password_reset_tokens (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    token_hash VARCHAR(64) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    used_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_password_reset_tokens PRIMARY KEY (id), 
    CONSTRAINT fk_password_reset_tokens_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_password_reset_tokens_token_hash UNIQUE (token_hash)
);

CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);

CREATE TABLE readings (
    id SERIAL NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    slug VARCHAR(140) NOT NULL, 
    summary VARCHAR(300) NOT NULL, 
    category_id INTEGER NOT NULL, 
    difficulty SMALLINT NOT NULL, 
    min_age SMALLINT NOT NULL, 
    max_age SMALLINT NOT NULL, 
    length VARCHAR(40) NOT NULL, 
    comprehension_focus VARCHAR(40) NOT NULL, 
    cover_emoji VARCHAR(16) NOT NULL, 
    cover_color VARCHAR(9) NOT NULL, 
    is_published BOOLEAN DEFAULT 'true' NOT NULL, 
    created_by_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_readings PRIMARY KEY (id), 
    CONSTRAINT ck_readings_difficulty_range CHECK (difficulty BETWEEN 1 AND 3), 
    CONSTRAINT ck_readings_age_order CHECK (min_age <= max_age), 
    CONSTRAINT ck_readings_age_range CHECK (min_age BETWEEN 4 AND 12 AND max_age BETWEEN 4 AND 12), 
    CONSTRAINT fk_readings_category_id_categories FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE RESTRICT, 
    CONSTRAINT fk_readings_created_by_id_users FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT uq_readings_slug UNIQUE (slug), 
    CONSTRAINT ck_readings_reading_length CHECK (length IN ('short', 'medium', 'long')), 
    CONSTRAINT ck_readings_comprehension_level CHECK (comprehension_focus IN ('literal', 'inferential', 'critical'))
);

CREATE INDEX ix_readings_category_id ON readings (category_id);

CREATE INDEX ix_readings_is_published ON readings (is_published);

CREATE TABLE revoked_tokens (
    jti VARCHAR(64) NOT NULL, 
    user_id INTEGER NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_revoked_tokens PRIMARY KEY (jti), 
    CONSTRAINT fk_revoked_tokens_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_revoked_tokens_expires_at ON revoked_tokens (expires_at);

CREATE INDEX ix_revoked_tokens_user_id ON revoked_tokens (user_id);

CREATE TABLE activities (
    id SERIAL NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    slug VARCHAR(140) NOT NULL, 
    activity_type VARCHAR(40) NOT NULL, 
    skill VARCHAR(40) NOT NULL, 
    difficulty SMALLINT NOT NULL, 
    instructions VARCHAR(400) NOT NULL, 
    icon VARCHAR(16) NOT NULL, 
    points_reward INTEGER NOT NULL, 
    reading_id INTEGER, 
    is_published BOOLEAN DEFAULT 'true' NOT NULL, 
    created_by_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_activities PRIMARY KEY (id), 
    CONSTRAINT ck_activities_difficulty_range CHECK (difficulty BETWEEN 1 AND 3), 
    CONSTRAINT ck_activities_points_range CHECK (points_reward BETWEEN 1 AND 100), 
    CONSTRAINT fk_activities_created_by_id_users FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT fk_activities_reading_id_readings FOREIGN KEY(reading_id) REFERENCES readings (id) ON DELETE SET NULL, 
    CONSTRAINT uq_activities_slug UNIQUE (slug), 
    CONSTRAINT ck_activities_activity_type CHECK (activity_type IN ('syllables', 'word_recognition', 'sentence_building', 'image_word', 'complete_word', 'sequence_order', 'rhymes', 'reading_comprehension')), 
    CONSTRAINT ck_activities_skill CHECK (skill IN ('phonological_awareness', 'word_recognition', 'vocabulary', 'sentence_building', 'sequencing', 'literal', 'inferential', 'critical'))
);

CREATE INDEX ix_activities_activity_type ON activities (activity_type);

CREATE INDEX ix_activities_is_published ON activities (is_published);

CREATE INDEX ix_activities_reading_id ON activities (reading_id);

CREATE INDEX ix_activities_skill ON activities (skill);

CREATE TABLE reading_paragraphs (
    id SERIAL NOT NULL, 
    reading_id INTEGER NOT NULL, 
    position SMALLINT NOT NULL, 
    text TEXT NOT NULL, 
    illustration VARCHAR(32), 
    image_url VARCHAR(500), 
    CONSTRAINT pk_reading_paragraphs PRIMARY KEY (id), 
    CONSTRAINT fk_reading_paragraphs_reading_id_readings FOREIGN KEY(reading_id) REFERENCES readings (id) ON DELETE CASCADE, 
    CONSTRAINT uq_paragraph_position UNIQUE (reading_id, position)
);

CREATE INDEX ix_reading_paragraphs_reading_id ON reading_paragraphs (reading_id);

CREATE TABLE student_profiles (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    display_name VARCHAR(40) NOT NULL, 
    avatar VARCHAR(40) DEFAULT 'owl' NOT NULL, 
    age SMALLINT, 
    classroom_id INTEGER, 
    created_by_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_student_profiles PRIMARY KEY (id), 
    CONSTRAINT ck_student_profiles_age_range CHECK (age IS NULL OR (age BETWEEN 4 AND 12)), 
    CONSTRAINT fk_student_profiles_classroom_id_classrooms FOREIGN KEY(classroom_id) REFERENCES classrooms (id) ON DELETE SET NULL, 
    CONSTRAINT fk_student_profiles_created_by_id_users FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT fk_student_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_student_profiles_user_id UNIQUE (user_id)
);

CREATE INDEX ix_student_profiles_classroom_id ON student_profiles (classroom_id);

CREATE TABLE attempts (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    activity_id INTEGER NOT NULL, 
    attempt_number SMALLINT NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    total_questions SMALLINT NOT NULL, 
    correct_first_try SMALLINT, 
    score NUMERIC(5, 2), 
    points_awarded INTEGER DEFAULT '0' NOT NULL, 
    CONSTRAINT pk_attempts PRIMARY KEY (id), 
    CONSTRAINT ck_attempts_score_range CHECK (score IS NULL OR (score BETWEEN 0 AND 100)), 
    CONSTRAINT fk_attempts_activity_id_activities FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    CONSTRAINT fk_attempts_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
    CONSTRAINT ck_attempts_attempt_status CHECK (status IN ('in_progress', 'completed'))
);

CREATE INDEX ix_attempts_student_activity ON attempts (student_id, activity_id);

CREATE TABLE guardian_students (
    guardian_id INTEGER NOT NULL, 
    student_id INTEGER NOT NULL, 
    relationship_label VARCHAR(40), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_guardian_students PRIMARY KEY (guardian_id, student_id), 
    CONSTRAINT fk_guardian_students_guardian_id_users FOREIGN KEY(guardian_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT fk_guardian_students_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE
);

CREATE INDEX ix_guardian_students_student_id ON guardian_students (student_id);

CREATE TABLE questions (
    id SERIAL NOT NULL, 
    activity_id INTEGER NOT NULL, 
    position SMALLINT NOT NULL, 
    prompt VARCHAR(400) NOT NULL, 
    prompt_illustration VARCHAR(32), 
    question_type VARCHAR(40) NOT NULL, 
    skill VARCHAR(40) NOT NULL, 
    hint VARCHAR(300), 
    explanation VARCHAR(400) NOT NULL, 
    CONSTRAINT pk_questions PRIMARY KEY (id), 
    CONSTRAINT fk_questions_activity_id_activities FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    CONSTRAINT uq_question_position UNIQUE (activity_id, position), 
    CONSTRAINT ck_questions_question_type CHECK (question_type IN ('single_choice', 'ordering')), 
    CONSTRAINT ck_questions_skill CHECK (skill IN ('phonological_awareness', 'word_recognition', 'vocabulary', 'sentence_building', 'sequencing', 'literal', 'inferential', 'critical'))
);

CREATE INDEX ix_questions_activity_id ON questions (activity_id);

CREATE INDEX ix_questions_skill ON questions (skill);

CREATE TABLE reading_sessions (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    reading_id INTEGER NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    points_awarded INTEGER DEFAULT '0' NOT NULL, 
    CONSTRAINT pk_reading_sessions PRIMARY KEY (id), 
    CONSTRAINT fk_reading_sessions_reading_id_readings FOREIGN KEY(reading_id) REFERENCES readings (id) ON DELETE CASCADE, 
    CONSTRAINT fk_reading_sessions_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE
);

CREATE INDEX ix_reading_sessions_student_reading ON reading_sessions (student_id, reading_id);

CREATE TABLE student_badges (
    student_id INTEGER NOT NULL, 
    badge_id INTEGER NOT NULL, 
    awarded_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_student_badges PRIMARY KEY (student_id, badge_id), 
    CONSTRAINT fk_student_badges_badge_id_badges FOREIGN KEY(badge_id) REFERENCES badges (id) ON DELETE CASCADE, 
    CONSTRAINT fk_student_badges_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE
);

CREATE TABLE student_challenges (
    student_id INTEGER NOT NULL, 
    challenge_id INTEGER NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_student_challenges PRIMARY KEY (student_id, challenge_id), 
    CONSTRAINT fk_student_challenges_challenge_id_challenges FOREIGN KEY(challenge_id) REFERENCES challenges (id) ON DELETE CASCADE, 
    CONSTRAINT fk_student_challenges_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE
);

CREATE TABLE student_link_codes (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    code_hash VARCHAR(64) NOT NULL, 
    created_by_id INTEGER, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    used_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_student_link_codes PRIMARY KEY (id), 
    CONSTRAINT fk_student_link_codes_created_by_id_users FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT fk_student_link_codes_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
    CONSTRAINT uq_student_link_codes_code_hash UNIQUE (code_hash)
);

CREATE INDEX ix_student_link_codes_student_id ON student_link_codes (student_id);

CREATE TABLE answer_options (
    id SERIAL NOT NULL, 
    question_id INTEGER NOT NULL, 
    position SMALLINT NOT NULL, 
    text VARCHAR(200) NOT NULL, 
    illustration VARCHAR(32), 
    is_correct BOOLEAN DEFAULT 'false' NOT NULL, 
    correct_position SMALLINT, 
    CONSTRAINT pk_answer_options PRIMARY KEY (id), 
    CONSTRAINT ck_answer_options_correct_position_positive CHECK (correct_position IS NULL OR correct_position >= 1), 
    CONSTRAINT fk_answer_options_question_id_questions FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE, 
    CONSTRAINT uq_option_position UNIQUE (question_id, position)
);

CREATE INDEX ix_answer_options_question_id ON answer_options (question_id);

CREATE TABLE point_transactions (
    id SERIAL NOT NULL, 
    student_id INTEGER NOT NULL, 
    amount INTEGER NOT NULL, 
    reason VARCHAR(40) NOT NULL, 
    description VARCHAR(200) NOT NULL, 
    attempt_id INTEGER, 
    reading_session_id INTEGER, 
    badge_id INTEGER, 
    challenge_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_point_transactions PRIMARY KEY (id), 
    CONSTRAINT ck_point_transactions_amount_positive CHECK (amount > 0), 
    CONSTRAINT fk_point_transactions_attempt_id_attempts FOREIGN KEY(attempt_id) REFERENCES attempts (id) ON DELETE SET NULL, 
    CONSTRAINT fk_point_transactions_badge_id_badges FOREIGN KEY(badge_id) REFERENCES badges (id) ON DELETE SET NULL, 
    CONSTRAINT fk_point_transactions_challenge_id_challenges FOREIGN KEY(challenge_id) REFERENCES challenges (id) ON DELETE SET NULL, 
    CONSTRAINT fk_point_transactions_reading_session_id_reading_sessions FOREIGN KEY(reading_session_id) REFERENCES reading_sessions (id) ON DELETE SET NULL, 
    CONSTRAINT fk_point_transactions_student_id_student_profiles FOREIGN KEY(student_id) REFERENCES student_profiles (id) ON DELETE CASCADE, 
    CONSTRAINT ck_point_transactions_point_reason CHECK (reason IN ('reading_completed', 'activity_completed', 'badge_earned', 'challenge_completed'))
);

CREATE INDEX ix_point_transactions_created_at ON point_transactions (created_at);

CREATE INDEX ix_point_transactions_student_id ON point_transactions (student_id);

CREATE TABLE attempt_answers (
    id SERIAL NOT NULL, 
    attempt_id INTEGER NOT NULL, 
    question_id INTEGER NOT NULL, 
    try_number SMALLINT NOT NULL, 
    selected_option_id INTEGER, 
    ordered_option_ids INTEGER[], 
    is_correct BOOLEAN NOT NULL, 
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    CONSTRAINT pk_attempt_answers PRIMARY KEY (id), 
    CONSTRAINT fk_attempt_answers_attempt_id_attempts FOREIGN KEY(attempt_id) REFERENCES attempts (id) ON DELETE CASCADE, 
    CONSTRAINT fk_attempt_answers_question_id_questions FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE, 
    CONSTRAINT fk_attempt_answers_selected_option_id_answer_options FOREIGN KEY(selected_option_id) REFERENCES answer_options (id) ON DELETE SET NULL, 
    CONSTRAINT uq_answer_try UNIQUE (attempt_id, question_id, try_number)
);

CREATE INDEX ix_attempt_answers_attempt_id ON attempt_answers (attempt_id);

CREATE INDEX ix_attempt_answers_question_id ON attempt_answers (question_id);

INSERT INTO alembic_version (version_num) VALUES ('90c1187fc692') RETURNING alembic_version.version_num;

COMMIT;

