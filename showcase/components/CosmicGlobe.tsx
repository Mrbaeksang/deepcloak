"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function DotSphere({ radius = 1.6, count = 1400 }: { radius?: number; count?: number }) {
  const group = useRef<THREE.Group>(null!);

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      // even-ish distribution on a sphere (golden spiral)
      const phi = Math.acos(1 - (2 * (i + 0.5)) / count);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      arr[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = radius * Math.cos(phi);
    }
    return arr;
  }, [radius, count]);

  useFrame((_, delta) => {
    if (group.current) {
      group.current.rotation.y += delta * 0.12;
      group.current.rotation.x += delta * 0.02;
    }
  });

  return (
    <group ref={group}>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial color="#a855f7" size={0.022} sizeAttenuation transparent opacity={0.9} />
      </points>
      <mesh>
        <sphereGeometry args={[radius, 32, 32]} />
        <meshBasicMaterial color="#853bce" wireframe transparent opacity={0.06} />
      </mesh>
    </group>
  );
}

export default function CosmicGlobe() {
  return (
    <Canvas camera={{ position: [0, 0, 4], fov: 70 }} dpr={[1, 2]} gl={{ antialias: true, alpha: true }}>
      <DotSphere />
    </Canvas>
  );
}
