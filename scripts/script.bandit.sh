(
cd github.com/indigo-dc/udocker &&
    bandit -f json --quiet  --confidence-level high --severity-level high --recursive .
)