import { ActivityType, ComprehensionLevel, ReadingLength, Role, Skill, SkillStatus } from './api.models';

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administrador', teacher: 'Docente', guardian: 'Acudiente', student: 'Estudiante',
};

export const SKILL_LABELS: Record<Skill, string> = {
  phonological_awareness: 'Sílabas y rimas',
  word_recognition: 'Reconocer palabras',
  vocabulary: 'Vocabulario',
  sentence_building: 'Formar oraciones',
  sequencing: 'Secuencias',
  literal: 'Comprensión literal',
  inferential: 'Comprensión inferencial',
  critical: 'Comprensión crítica',
};

export const SKILL_STATUS_LABELS: Record<SkillStatus, string> = {
  strong: 'Fortalecida', developing: 'En desarrollo', needs_support: 'Necesita refuerzo', not_started: 'Sin datos',
};

export const COMPREHENSION_LABELS: Record<ComprehensionLevel, string> = {
  literal: 'Literal', inferential: 'Inferencial', critical: 'Crítica',
};

export const LENGTH_LABELS: Record<ReadingLength, string> = { short: 'Corta', medium: 'Mediana', long: 'Larga' };

export const DIFFICULTY_LABELS: Record<number, string> = { 1: 'Fácil', 2: 'Intermedio', 3: 'Reto' };

export const ACTIVITY_TYPE_LABELS: Record<ActivityType, string> = {
  syllables: 'Sílabas', word_recognition: 'Reconocer palabras', sentence_building: 'Formar oraciones',
  image_word: 'Imagen y palabra', complete_word: 'Completar palabras', sequence_order: 'Ordenar secuencias',
  rhymes: 'Rimas', reading_comprehension: 'Comprensión de textos',
};

/** Avatares: el código se guarda en la base de datos; el desbloqueo lo decide el backend. */
export const AVATAR_ICONS: Record<string, string> = {
  owl: '🦉', cat: '🐱', dog: '🐶', bunny: '🐰', fox: '🦊', panda: '🐼', lion: '🦁',
  unicorn: '🦄', dragon: '🐉', astronaut: '🧑‍🚀',
};

export const avatarIcon = (code: string | null | undefined): string => AVATAR_ICONS[code ?? ''] ?? '🦉';
