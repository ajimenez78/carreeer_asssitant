import { Workspace } from "../components/workspace";
import { SessionGate } from "../components/session-gate";
export default function Home() { return <SessionGate><Workspace /></SessionGate>; }
