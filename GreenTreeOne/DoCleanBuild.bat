@echo on
del *.json /s
del *.pyc /s
python -m beheaded -R .
python -m build
