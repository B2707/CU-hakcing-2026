# Emergency classifier build.
#
#   make            native build (your laptop, for testing)
#   make qnx        cross-compile for QNX aarch64 (Raspberry Pi 5)
#   make retrain    regenerate model.h from emergency_data.csv, then build
#   make test       build and run a few sample utterances
#   make clean

CFLAGS = -O2 -Wall -Wextra
LDLIBS = -lm

HEADERS = model.h keyword_override.h wake_word.h cancel_word.h

classifier: classifier.c $(HEADERS)
	$(CC) $(CFLAGS) -o $@ classifier.c $(LDLIBS)

# interactive tester: prompts repeatedly, shows full probability breakdown
interactive: interactive.c model.h keyword_override.h wake_word.h
	$(CC) $(CFLAGS) -o $@ interactive.c $(LDLIBS)

# --- QNX cross build ------------------------------------------------------
# Requires the QNX SDP environment sourced first:
#   source ~/qnx800/qnxsdp-env.sh
# That puts qcc / the aarch64 toolchain on PATH.
QNX_CC = qcc -Vgcc_ntoaarch64le
qnx: classifier.c $(HEADERS)
	$(QNX_CC) $(CFLAGS) -o classifier_qnx classifier.c -lm

retrain:
	python3 train.py
	$(MAKE) classifier

# Raw classifier smoke test (no wake gate): the underlying model still works.
test: classifier
	@printf '%s\n' \
	  "I'm lost in the woods" \
	  "my arm is broken" \
	  "there's smoke everywhere" \
	  "i'm stuck and can't get out" \
	  "what's the weather today" \
	  | ./classifier --raw

# Wake-gate test: proves "hey rocko help" is the single choke point.
# No-wake lines print NOTHING; the wake phrase (and its variants) opens it,
# phrase-alone -> sos, wake-gated cancel -> stop.
gate-test: classifier
	@echo "--- gated (each line should react per its label) ---"
	@printf '%s\n' \
	  "hey rocko help" \
	  "hey rocko help i am stuck and cannot get out" \
	  "HEY, ROCCO! HELP, the kitchen is on fire" \
	  "hey roko help my arm is broken and bleeding" \
	  "hey rocko help i am okay stop" \
	  | ./classifier
	@echo "--- NOT gated (each line MUST print nothing) ---"
	@printf '%s\n' \
	  "i am trapped and my leg is injured help me" \
	  "somebody please help help help" \
	  "what is the weather today" \
	  | ./classifier
	@echo "--- end (blank above = gate held) ---"

clean:
	rm -f classifier classifier_qnx interactive

.PHONY: qnx retrain test gate-test clean
