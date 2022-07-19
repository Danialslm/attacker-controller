pid=$(ps -ef | grep -v grep | grep attacker_controller | awk '{print $2}')

if [ ! -z $pid ]; then
  kill -9 $pid
fi

PROJECT_PATH=$(dirname $(cd "$(dirname "$0")" && pwd))
export PYTHONPATH=$PROJECT_PATH

$PROJECT_PATH/.venv/bin/python $PROJECT_PATH/attacker_controller
