import { notFound } from "next/navigation";
import Dashboard from "../../components/dashboard";
const sections = new Set([
  "discover",
  "research",
  "campaigns",
  "assets",
  "production",
  "review",
  "distribution",
  "community",
  "analytics",
  "learning",
]);
export default async function Page({
  params,
}: {
  params: Promise<{ workspace?: string[] }>;
}) {
  const { workspace = [] } = await params;
  if (workspace.length > 2 || (workspace[0] && !sections.has(workspace[0])))
    notFound();
  return <Dashboard />;
}
