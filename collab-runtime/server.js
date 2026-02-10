function broadcast(msg) {
  const data = JSON.stringify(msg);
  wsClients.forEach((ws) => {
    if (ws.readyState === 1) ws.send(data);
  });
}
