#!/usr/bin/env bash
# run_scenarios.sh – execute all bot.py scenarios via curl
# Usage: ./run_scenarios.sh <ngrok-url>
# Example: ./run_scenarios.sh https://abcd1234.ngrok.io

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <ngrok-url>"
    exit 1
fi

NGROK_URL="$1"

scenarios=(
    schedule_appointment
    reschedule_appointment
    cancel_appointment
    medication_refill
    location_questions
    insurance_questions
    weekend_appointment
    midnight_appointment
    wrong_number
    angry_patient
    emergency  # if you have an 'emergency' route; adjust/remove as needed
)

echo "Sending requests to $NGROK_URL …"

for scen in "${scenarios[@]}"; do
    echo -n "  → $scen: "
    curl -sf "${NGROK_URL}/call?scenario=${scen}" \
        && echo "OK" || echo "FAILED"
    # short sleep in case the service needs a moment
    sleep 0.5
done

echo "done."