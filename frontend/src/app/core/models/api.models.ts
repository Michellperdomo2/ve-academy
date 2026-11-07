/** Tipos que reflejan los esquemas Pydantic del backend (app/schemas). */

export type Role = 'admin' | 'teacher' | 'guardian' | 'student';
export type Skill =
  | 'phonological_awareness' | 'word_recognition' | 'vocabulary' | 'sentence_building'
  | 'sequencing' | 'literal' | 'inferential' | 'critical';
export type ComprehensionLevel = 'literal' | 'inferential' | 'critical';
export type ReadingLength = 'short' | 'medium' | 'long';
export type ActivityType =
  | 'syllables' | 'word_recognition' | 'sentence_building' | 'image_word'
  | 'complete_word' | 'sequence_order' | 'rhymes' | 'reading_comprehension';
export type QuestionType = 'single_choice' | 'ordering';
export type SkillStatus = 'strong' | 'developing' | 'needs_support' | 'not_started';

export interface ApiError { error: { code: string; message: string; details?: unknown } }
export interface Page<T> { items: T[]; total: number; page: number; size: number }
export interface Message { message: string }

export interface User {
  id: number; username: string; email: string | null; full_name: string; role: Role;
  is_active: boolean; created_at: string; last_login_at: string | null; student_profile_id: number | null;
}
export interface TokenResponse { access_token: string; token_type: string; expires_at: string; user: User }

export interface Classroom {
  id: number; name: string; grade: string; school_year: number; institution: string | null;
  teacher_id: number; teacher_name: string; student_count: number;
}
export interface Student {
  id: number; user_id: number; username: string; display_name: string; avatar: string; age: number | null;
  is_active: boolean; classroom_id: number | null; classroom_name: string | null; guardian_names: string[];
  total_points: number; level_number: number; created_at: string;
}

export interface Category { id: number; name: string; slug: string; description: string | null; icon: string | null }
export interface Paragraph { id: number; position: number; text: string; illustration: string | null; image_url: string | null }
export interface ReadingSummary {
  id: number; title: string; slug: string; summary: string; category: Category; difficulty: number;
  min_age: number; max_age: number; length: ReadingLength; comprehension_focus: ComprehensionLevel;
  cover_emoji: string; cover_color: string; is_published: boolean; word_count: number; completed_by_me: boolean | null;
}
export interface ReadingDetail extends ReadingSummary {
  paragraphs: Paragraph[]; activity_ids: number[]; created_at: string; updated_at: string;
}
export interface ReadingWrite {
  title: string; summary: string; category_id: number; difficulty: number; min_age: number; max_age: number;
  comprehension_focus: ComprehensionLevel; cover_emoji: string; cover_color: string; is_published: boolean;
  paragraphs: { text: string; illustration: string | null; image_url?: string | null }[];
}
export interface BadgeBrief { id: number; code: string; name: string; icon: string }
export interface ChallengeBrief { id: number; title: string; icon: string; points_reward: number }
export interface ReadingCompletion {
  session: { id: number; reading_id: number; points_awarded: number };
  points_awarded: number; first_time: boolean; new_badges: BadgeBrief[];
  completed_challenges: ChallengeBrief[]; next_activity_id: number | null;
}

export interface ActivitySummary {
  id: number; title: string; slug: string; activity_type: ActivityType; skill: Skill; difficulty: number;
  instructions: string; icon: string; points_reward: number; reading_id: number | null; is_published: boolean;
  question_count: number; best_score: number | null;
}
export interface OptionPublic { id: number; text: string; illustration: string | null }
export interface QuestionPublic {
  id: number; position: number; prompt: string; prompt_illustration: string | null;
  question_type: QuestionType; skill: Skill; has_hint: boolean; options: OptionPublic[];
}
export interface ActivityDetail extends ActivitySummary { reading_title: string | null; questions: QuestionPublic[] }
export interface OptionAdmin extends OptionPublic { is_correct: boolean; correct_position: number | null }
export interface QuestionAdmin {
  id: number; position: number; prompt: string; prompt_illustration: string | null; question_type: QuestionType;
  skill: Skill; hint: string | null; explanation: string; options: OptionAdmin[];
}
export interface ActivityAdminDetail extends ActivitySummary { reading_title: string | null; attempt_count: number; questions: QuestionAdmin[] }
export interface ActivityWrite {
  title: string; activity_type: ActivityType; skill: Skill; difficulty: number; instructions: string; icon: string;
  points_reward: number; reading_id: number | null; is_published: boolean;
  questions: {
    prompt: string; prompt_illustration: string | null; question_type: QuestionType; skill: Skill;
    hint: string | null; explanation: string;
    options: { text: string; illustration: string | null; is_correct: boolean; correct_position: number | null }[];
  }[];
}

export interface AttemptStart { attempt_id: number; attempt_number: number; total_questions: number }
export interface AnswerFeedback {
  is_correct: boolean; try_number: number; message: string; explanation: string | null; hint: string | null;
  correct_option_ids: number[] | null; can_retry: boolean;
}
export interface Recommendation { activity_id: number; title: string; icon: string; skill: Skill; reason: string }
export interface Level { id: number; number: number; name: string; min_points: number; icon: string }
export interface AttemptResult {
  attempt_id: number; activity_id: number; total_questions: number; correct_first_try: number; score: number;
  points_awarded: number; message: string; stars: number; new_badges: BadgeBrief[];
  completed_challenges: ChallengeBrief[]; level_up: Level | null; recommendations: Recommendation[];
}
export interface AttemptHistoryItem {
  attempt_id: number; activity_id: number; activity_title: string; activity_type: ActivityType; skill: Skill;
  attempt_number: number; status: string; score: number | null; correct_first_try: number | null;
  total_questions: number; total_tries: number; points_awarded: number; started_at: string; completed_at: string | null;
}
export interface ReadingHistoryItem {
  session_id: number; reading_id: number; reading_title: string; cover_emoji: string; completed_at: string; points_awarded: number;
}
export interface SkillProgress {
  skill: Skill; label: string; answered: number; correct_first_try: number; accuracy: number | null; status: SkillStatus;
}
export interface DailyActivity { date: string; readings: number; activities: number; points: number }
export interface ProgressSummary {
  student_id: number; display_name: string; avatar: string; total_points: number; level: Level; next_level: Level | null;
  points_to_next_level: number | null; readings_completed: number; readings_total: number; activities_completed: number;
  activities_total: number; progress_percent: number; total_attempts: number; total_answers: number;
  correct_answers: number; incorrect_answers: number; average_score: number | null; badges_earned: number;
  skills: SkillProgress[]; strengths: string[]; needs_support: string[]; recommendations: Recommendation[];
  weekly_activity: DailyActivity[];
}
export interface StudentDashboard {
  greeting: string; progress: ProgressSummary;
  continue_reading: { id: number; title: string; cover_emoji: string; cover_color: string; difficulty: number }[];
  suggested_activities: { id: number; title: string; icon: string; reason: string; skill_label: string }[];
  active_challenges: { id: number; title: string; icon: string; progress: number; target: number; points_reward: number }[];
  recent_badges: BadgeBrief[];
}
export interface Badge {
  id: number; code: string; name: string; description: string; icon: string; criteria_type: string;
  criteria_value: number; criteria_skill: Skill | null; points_bonus: number; is_active: boolean;
}
export interface StudentBadge { badge: Badge; earned: boolean; awarded_at: string | null; progress: number; target: number }
export interface Challenge {
  id: number; title: string; description: string; icon: string; challenge_type: string; target: number;
  skill: Skill | null; points_reward: number; is_active: boolean;
}
export interface StudentChallenge { challenge: Challenge; progress: number; completed: boolean; completed_at: string | null }
export interface Reward { id: number; code: string; name: string; kind: 'avatar' | 'sticker'; icon: string; required_level: number; unlocked: boolean }

export interface OverviewStats {
  users_by_role: Record<string, number | undefined>; active_students_7d: number; readings_published: number;
  activities_published: number; reading_sessions_completed: number; attempts_completed: number;
  average_score: number | null; skills: SkillProgress[]; ai_companion_enabled: boolean;
}
export interface ClassroomStudentRow {
  student_id: number; display_name: string; avatar: string; total_points: number; level_number: number;
  readings_completed: number; activities_completed: number; average_score: number | null;
  needs_support: string[]; last_activity_at: string | null;
}
export interface ClassroomStats {
  classroom_id: number; classroom_name: string; student_count: number; average_score: number | null;
  skills: SkillProgress[]; students: ClassroomStudentRow[];
}
export interface CompanionStatus { enabled: boolean; provider: string; available: boolean; message: string }
