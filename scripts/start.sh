pid=$(ps -ef | grep -v grep | grep attacker_controller | awk '{print $2}')

if [ ! -z $pid ]; then
  kill -9 $pid
fi

PROJECT_PATH=$(dirname $(cd "$(dirname "$0")" && pwd))
export PYTHONPATH=$PROJECT_PATH

source $PROJECT_PATH/.venv/bin/activate

python $PROJECT_PATH/attacker_controller
