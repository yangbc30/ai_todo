backend(fastapi) 


```cmd
conda activate memo_backend
conda install -c conda-forge fastapi uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

test http://127.0.0.1:8000/docs



frontend

```cmd
npx @react-native-community/cli init SimpleMemoApp
cd SimpleMemoApp
npx react-native run-android
```