Process k8s : 

1- 
kubectl delete deployments,services,configmaps,secrets,pvc –all

2-
docker build -t chat-stock-market-api:latest ./market-api
docker build -t chat-stock-backend:latest ./chat-backend
docker build -t chat-stock-frontend:latest ./chat-frontend

3-
kubectl create secret generic chat-stock-secrets \
  --from-literal=HF_TOKEN='TON_HF_TOKEN' \
  --from-literal=FINNHUB_API_KEY='TA_CLE_FINNHUB' \
  --from-literal=GF_SECURITY_ADMIN_PASSWORD='TON_MDP_GRAFANA' \
  -o yaml --dry-run=client | kubectl apply -f -

4-
kubectl apply -f ./k8s


5-
kubectl rollout restart deploy/market-api deploy/grafana

6-
kubectl port-forward svc/frontend-service 9090:5173
kubectl port-forward svc/backend-service 8000:8000
kubectl port-forward svc/prometheus-service 9091:9090
kubectl port-forward svc/grafana-service 3000:3000
kubectl proxy (pour avoir accès au Dashboard k8s)


Accès front

Prometheus → http://localhost:9091

Dashboard → http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/pod?namespace=default

Grafana → http://localhost:3000

Frontend → http://localhost:5173


