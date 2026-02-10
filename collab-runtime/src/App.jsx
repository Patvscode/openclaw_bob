import React, { useEffect, useState } from 'react';
import GridLayout from 'react-grid-layout';
import DynamicHost from './DynamicHost.jsx';
import './App.css';

const wsUrl = 'ws://' + (window.location.hostname || 'localhost') + ':3000/ws';

export default function App() {
  const [panels, setPanels] = useState([]); // each panel: {id, x, y, w, h, componentSpec}

  // WebSocket handling for UI commands from the backend
  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.type === 'addPanel') {
        setPanels((prev) => [...prev, data.payload]);
      } else if (data.type === 'removePanel') {
        setPanels((prev) => prev.filter((p) => p.id !== data.payload.id));
      } else if (data.type === 'updatePanel') {
        setPanels((prev) =>
          prev.map((p) => (p.id === data.payload.id ? { ...p, ...data.payload } : p))
        );
      }
    };
    return () => ws.close();
  }, []);

  const layout = panels.map((p) => ({ i: p.id, x: p.x, y: p.y, w: p.w, h: p.h }));

  return (
    <div className="app-container">
      <GridLayout className="layout" layout={layout} cols={12} rowHeight={30} width={1200}>
        {panels.map((p) => (
          <div key={p.id} data-grid={p} className="panel">
            <h3>{p.title}</h3>
            <DynamicHost spec={p.componentSpec} />
          </div>
        ))}
      </GridLayout>
    </div>
  );
}
