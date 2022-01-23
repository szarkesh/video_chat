### Project Setup (Mac)
1. Install `python3`, `CMake` and `poetry`
  - `brew install python3 cmake poetry`
2. Install packages local to project
  - `poetry install`
3. To run processing demo: `cd processing && poetry run python main.py`



### Project Setup (Windows)
1. Install Python
2. Install CMake from online installer 
3. Install Visual Studio C++ tools (compiler) & restart
4. pip install cmake
5. pip install numpy
6. pip install dlib (can take 5+ mins)
7. now sohuld be able to run example facial recognition, in cmd at project root: python raymond.py shape_predictor_68_face_landmarks.dat faces
