import React, { useEffect, useState } from 'react';
import { VM } from 'vm2';

/**
 * `spec` is a plain object that describes the component to render.
 * Example:
 *   {
 *     "type": "MonacoEditor",
 *     "props": { "language": "python", "value": "print('hi')" }
 *   }
 * The back‑end can send any allowed component type. For safety we keep a whitelist.
 */

const componentWhitelist = {
  MonacoEditor: React.lazy(() => import('@monaco-editor/react')),
  Iframe: (props) => <iframe {...props} style={{ width: '100%', height: '100%' }} />,
  ConsoleLog: (props) => <pre>{props.text}</pre>,
  // Add more components here as we integrate them.
};

export default function DynamicHost({ spec }) {
  const [error, setError] = useState(null);
  const [Component, setComponent] = useState(null);

  useEffect(() => {
    if (!spec || !spec.type) return;
    if (!componentWhitelist[spec.type]) {
      setError(`Component type "${spec.type}" not allowed`);
      return;
    }
    // Lazy‑load the component if it is a dynamic import
    setComponent(componentWhitelist[spec.type]);
  }, [spec]);

  if (error) return <div className="error">{error}</div>;
  if (!Component) return null;

  return (
    <React.Suspense fallback={<div>Loading…</div>}>
      <Component {...spec.props} />
    </React.Suspense>
  );
}
