/*
 * Cancel words: a wake-gated "stop" / "cancel" / "clear" / "ok" / "okay"
 * cancels the beacon's emergency queue. This wins over any classifier hit in
 * the same phrase (an explicit "I'm okay" must never be read as an emergency).
 *
 * Matching is whole-word and case-insensitive over the ALREADY-GATED phrase
 * (the text after the wake phrase), so it inherits the single choke point:
 * "stop" only cancels when preceded by "hey rocko help". These tokens mirror
 * transmitter.py's STOP_TOKENS so the surface side reads the same intent.
 */
#ifndef CANCEL_WORD_H
#define CANCEL_WORD_H

#include <ctype.h>
#include <string.h>

static const char *CANCEL_WORDS[] = {
    "stop", "cancel", "clear", "ok", "okay",
};
#define NUM_CANCEL_WORDS (sizeof(CANCEL_WORDS) / sizeof(CANCEL_WORDS[0]))

/* Whole-word, case-insensitive search for any cancel word. */
static int has_cancel_keyword(const char *text) {
    for (size_t k = 0; k < NUM_CANCEL_WORDS; k++) {
        const char *kw = CANCEL_WORDS[k];
        size_t klen = strlen(kw);
        for (const char *p = text; *p; p++) {
            size_t i = 0;
            while (i < klen && p[i] &&
                   (char)tolower((unsigned char)p[i]) == kw[i]) i++;
            if (i != klen) continue;
            char before = (p == text) ? ' ' : p[-1];
            char after = p[klen];
            int bound_before = !isalnum((unsigned char)before);
            int bound_after = (after == '\0') || !isalnum((unsigned char)after);
            if (bound_before && bound_after) return 1;
        }
    }
    return 0;
}

#endif /* CANCEL_WORD_H */
