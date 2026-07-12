#!/bin/sh
# Acceptance battery for the wake-gated cancel/distress resolution
# (rules 1-3, 2026-07-12 hardening). Every line MUST produce exactly its
# required outcome; any deviation exits nonzero so `make gate-test` / CI fails
# loudly. POSIX sh only (QNX ksh + dash clean).
#
# Usage: gate_battery.sh [path-to-classifier]      (default: ./classifier)
set -u
CLS="${1:-./classifier}"
fails=0

# first-token of the classifier's output for one transcript line
first() { printf '%s\n' "$1" | "$CLS" 2>/dev/null | head -n1 | cut -d' ' -f1; }

# expect_exact PHRASE CLASS  -> first token must equal CLASS
expect_exact() {
    got=$(first "$1")
    if [ "$got" = "$2" ]; then
        printf '  ok    %-8s <- %s\n' "$got" "$1"
    else
        printf '  FAIL  want=%-8s got=%-8s <- %s\n' "$2" "${got:-<silent>}" "$1"
        fails=$((fails + 1))
    fi
}

# expect_alarm PHRASE  -> first token must be an emergency class or sos
#   (NEVER stop, NEVER silent, NEVER none/uncertain)
expect_alarm() {
    got=$(first "$1")
    case "$got" in
        fire|injured|lost|trapped|sos)
            printf '  ok    %-8s <- %s\n' "$got" "$1" ;;
        *)
            printf '  FAIL  want=alarm  got=%-8s <- %s\n' "${got:-<silent>}" "$1"
            fails=$((fails + 1)) ;;
    esac
}

# expect_silent PHRASE -> classifier prints NOTHING (gate closed)
expect_silent() {
    got=$(printf '%s\n' "$1" | "$CLS" 2>/dev/null)
    if [ -z "$got" ]; then
        printf '  ok    <silent> <- %s\n' "$1"
    else
        printf '  FAIL  want=<silent> got=%s <- %s\n' "$got" "$1"
        fails=$((fails + 1))
    fi
}

echo "--- STOP required (explicit cancel, no negator) ---"
expect_exact "hey rocko help i am okay" stop
expect_exact "hey rocko help stop" stop
expect_exact "hey rocko help ok ok ok" stop
expect_exact "hey rocko help it is okay i got out i am fine" stop

echo "--- EMERGENCY or SOS required (never stop, never silent) ---"
expect_alarm "hey rocko help i am not okay"
expect_alarm "hey rocko help i am not fine i am hurt"
expect_alarm "hey rocko help nothing is okay"
expect_alarm "hey rocko help no i am not okay"
expect_alarm "hey rocko help i fell okay"
expect_alarm "hey rocko help i cannot move okay"
expect_alarm "hey rocko help i am injured but okay"

echo "--- specific class required ---"
expect_exact "hey rocko help i am trapped okay" trapped
expect_exact "hey rocko help everything is clear now i am trapped under a rock" trapped

echo "--- unchanged: phrase-alone SOS + no-wake silence ---"
expect_exact "hey rocko help" sos
expect_silent "i am trapped and my leg is injured help me"
expect_silent "somebody please help help help"
expect_silent "what is the weather today"

if [ "$fails" -eq 0 ]; then
    echo "battery: ALL PASS"
    exit 0
fi
echo "battery: $fails FAILED"
exit 1
