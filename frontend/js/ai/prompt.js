// The question sent to an AI about highlighted text: a saved, editable template.

const KEY = "japanese-reader:ai-template";

export const DEFAULT_TEMPLATE = `I'm learning Japanese. Explain the grammar of the highlighted part of this sentence. Be structured and concise.

Sentence: {{sentence}}
Highlighted: {{selection}}

1. Breakdown: split the highlighted part into words; give each word's reading in hiragana and its meaning.
2. Conjugations: for every verb or adjective that is conjugated, give
   - the dictionary form, its reading and meaning
   - its type (godan / ichidan / irregular verb, i-adjective, na-adjective)
   - the form used here (e.g. polite past, te-form, passive, potential)
   - the conjugation rule, step by step from the dictionary form
3. Grammar patterns: name each pattern used (e.g. 〜ている, 〜ので, 〜たら), what it means, and how it attaches to nouns, i-adjectives, na-adjectives and verbs (the connection rule for each).
4. Nuance: politeness level, and anything a learner might misread.
5. Two short example sentences using the same pattern, with English translations.

Answer in English. Write readings in brackets after kanji, e.g. 食[た]べる.
{{note}}`;

/** Fills the template. An empty note removes its line. */
export function fillPrompt(template, { selection, sentence, note = "" }) {
  const noteLine = note.trim() ? `Additional request: ${note.trim()}` : "";
  return template
    .replaceAll("{{selection}}", selection)
    .replaceAll("{{sentence}}", sentence)
    .replaceAll("{{note}}", noteLine)
    .trim();
}

const SENTENCE_END = /[。！？!?\n]/;

/** The sentence of `context` containing the text at `offset`, ending punctuation included. */
export function sentenceAround(context, offset) {
  let start = offset;
  while (start > 0 && !SENTENCE_END.test(context[start - 1])) start--;
  let end = offset;
  while (end < context.length && !SENTENCE_END.test(context[end])) end++;
  if (end < context.length && context[end] !== "\n") end++;
  return context.slice(start, end).trim();
}

export function loadTemplate() {
  try {
    return localStorage.getItem(KEY) || DEFAULT_TEMPLATE;
  } catch {
    return DEFAULT_TEMPLATE;
  }
}

export function saveTemplate(template) {
  try {
    localStorage.setItem(KEY, template);
    return true;
  } catch {
    return false;
  }
}

export function resetTemplate() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // Nothing saved, or storage unavailable: the default applies either way.
  }
  return DEFAULT_TEMPLATE;
}
