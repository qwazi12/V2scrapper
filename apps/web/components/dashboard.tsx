"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Aperture,
  ArrowDownToLine,
  ArrowRight,
  AudioLines,
  BarChart3,
  Bell,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clapperboard,
  Compass,
  Film,
  FlaskConical,
  FolderOpen,
  LayoutDashboard,
  Loader2,
  LogOut,
  Menu,
  MessageSquare,
  Play,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  ShieldOff,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";

// Database DTOs preserve nullable provider values and provenance. The runtime API schema is exported with the build.
interface Row {
  id: string;
  [key: string]: any;
}
interface Workspace {
  [key: string]: any;
  opportunities: Row[];
  campaigns: Row[];
  exports: Row[];
  variants: Row[];
  scripts: Row[];
  jobs: Row[];
  claims: Row[];
  evidence: Row[];
  rights: Row[];
  assets: Row[];
  publications: Row[];
  replies: Row[];
  experiments: Row[];
  quality: Row[];
}
const nav = [
  ["", "Control Room", LayoutDashboard],
  ["discover", "Discover", Compass],
  ["research", "Research Desk", BookOpen],
  ["campaigns", "Campaign Studio", Clapperboard],
  ["assets", "Asset Library", FolderOpen],
  ["production", "Production", Film],
  ["review", "Quality Review", ShieldCheck],
  ["distribution", "Distribution", Send],
  ["community", "Community", MessageSquare],
  ["analytics", "Analytics", BarChart3],
  ["learning", "Learning", FlaskConical],
] as const;
const formatName = (s: string) =>
  ({
    long_16_9: "Landscape · 16:9",
    short_9_16: "Short · 9:16",
    reel_9_16: "Reel · 9:16",
    carousel_4_5: "Carousel · 4:5",
  })[s] || s;
const shortHash = (s: string) => s?.slice(0, 12) + "…";
const time = (s: string) =>
  new Date(s).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
function Badge({
  value,
  children,
}: {
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <span className={"badge " + (value || "").replaceAll("_", "-")}>
      {children || value?.replaceAll("_", " ")}
    </span>
  );
}
function Empty({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <Aperture size={36} />
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      className={"button " + (secondary ? "secondary" : "")}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

export default function Dashboard() {
  const path = usePathname().split("/").filter(Boolean);
  const section = path[0] || "";
  const routeId = path[1];
  const router = useRouter();
  const [data, setData] = useState<Workspace | null>(null),
    [authMode, setAuthMode] = useState<{
      environment: string;
      local_login_allowed: boolean;
      oidc_configured: boolean;
    } | null>(null),
    [csrf, setCsrf] = useState(""),
    [signed, setSigned] = useState(false),
    [boot, setBoot] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [search, setSearch] = useState(""),
    [sidebar, setSidebar] = useState(false),
    [opModal, setOpModal] = useState(false),
    [operations, setOperations] = useState(false),
    [reviewNote, setReviewNote] = useState(""),
    [replyTexts, setReplyTexts] = useState<Record<string, string>>({}),
    [scriptText, setScriptText] = useState<Record<string, string>>({}),
    [packageExport, setPackageExport] = useState(""),
    [accountId, setAccountId] = useState(""),
    [packageTitle, setPackageTitle] = useState(""),
    [caption, setCaption] = useState(
      "Original fictional test story. This is a local mock publication.",
    ),
    [schedule, setSchedule] = useState(""),
    [lostResponse, setLostResponse] = useState(true),
    [selectedExport, setSelectedExport] = useState("");
  const load = useCallback(async () => {
    const r = await fetch("/api/v1/workspace");
    if (r.ok) {
      setData(await r.json());
      setError((previous) =>
        previous.startsWith("Connection interrupted") ? "" : previous,
      );
    } else if (r.status === 401) setSigned(false);
    else throw Error("The workspace could not load. Check the API and retry.");
  }, []);
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [r, auth] = await Promise.all([
          fetch("/api/v1/auth/session"),
          fetch("/api/v1/auth/config"),
        ]);
        if (auth.ok && active) setAuthMode(await auth.json());
        if (r.ok) {
          const s = await r.json();
          if (active) {
            setCsrf(s.csrf_token);
            setSigned(true);
            await load();
          }
        }
      } catch {
        if (active)
          setError(
            "The API is unavailable. Please retry when the service is healthy.",
          );
      } finally {
        if (active) setBoot(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [load]);
  useEffect(() => {
    if (!signed) return;
    const timer = setInterval(() => {
      load().catch(() =>
        setError("Connection interrupted. Retrying the local workspace…"),
      );
    }, 4000);
    return () => clearInterval(timer);
  }, [signed, load]);
  useEffect(() => {
    setSearch("");
    setSidebar(false);
    setError("");
  }, [section]);
  useEffect(() => {
    if (!opModal && !operations) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>(".modal");
    (
      dialog?.querySelector<HTMLElement>("input,textarea") ||
      dialog?.querySelector<HTMLElement>("button")
    )?.focus();
    const trap = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpModal(false);
        setOperations(false);
      }
      if (e.key === "Tab" && dialog) {
        const items = Array.from(
          dialog.querySelectorAll<HTMLElement>(
            "button:not(:disabled),input,textarea,select,a[href]",
          ),
        );
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [opModal, operations]);

  async function login() {
    setBusy(true);
    setError("");
    try {
      if (!authMode?.local_login_allowed) {
        const r = await fetch("/api/v1/auth/oidc/start");
        const result = await r.json();
        if (!r.ok) throw Error(result.message);
        window.location.assign(result.authorization_url);
        return;
      }
      const r = await fetch("/api/v1/auth/local", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const s = await r.json();
      if (!r.ok) throw Error(s.message);
      setCsrf(s.csrf_token);
      setSigned(true);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function act(
    action: string,
    target: string | null = null,
    payload: Record<string, unknown> = {},
    message = "Saved to the local workspace.",
  ): Promise<Row | null> {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await fetch("/api/v1/actions/" + action, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrf,
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({ target, payload }),
      });
      const result = await r.json();
      if (!r.ok) throw Error(`${result.code}: ${result.message}`);
      await load();
      setNotice(message);
      return result;
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  }
  async function createFixture() {
    const r = await act(
      "fixture",
      null,
      {},
      "Original test story created. Review its evidence before creating a campaign.",
    );
    if (r) router.push("/research/" + r.opportunity_id);
  }
  async function uploadImage(form: HTMLFormElement) {
    setBusy(true);
    setError("");
    try {
      const r = await fetch("/api/v1/assets/upload", {
        method: "POST",
        headers: {
          "X-CSRF-Token": csrf,
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: new FormData(form),
      });
      const result = await r.json();
      if (!r.ok) throw Error(result.message);
      await load();
      setNotice(
        "Image decoded and stored privately. Review ownership before selecting it for a render.",
      );
      form.reset();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const filtered = (rows: Row[]) =>
    rows.filter((r) =>
      JSON.stringify(r).toLowerCase().includes(search.toLowerCase()),
    );
  const link = (href: string, text: string) => (
    <Link className="text-link" href={href}>
      {text}
      <ArrowRight size={15} />
    </Link>
  );
  if (boot)
    return (
      <div className="login">
        <Loader2 className="spin" />
        <p>Opening your workspace…</p>
      </div>
    );
  if (!signed)
    return (
      <div className="login">
        <div className="login-card">
          <div className="brand-mark">
            <Play fill="currentColor" size={24} />
          </div>
          <span className="eyebrow">SCREEN CENTRAL OS</span>
          <h1>
            Your next great
            <br />
            story starts here.
          </h1>
          <p>
            A private workspace for thoughtful research, original production,
            and evidence-led growth.
          </p>
          <div className="login-safety">
            <ShieldCheck size={18} />
            <span>
              {authMode?.environment === "local"
                ? "Local development · no external credentials"
                : "Private workspace · owner Google sign-in"}
              <br />
              <small>Publishing and paid providers are disabled.</small>
            </span>
          </div>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <Button
            onClick={login}
            disabled={
              busy ||
              !authMode ||
              (!authMode.local_login_allowed && !authMode.oidc_configured)
            }
          >
            {busy ? (
              <Loader2 className="spin" size={18} />
            ) : (
              <ArrowRight size={18} />
            )}
            {authMode?.local_login_allowed
              ? "Enter local owner workspace"
              : "Sign in with Google"}
          </Button>
          <small className="fineprint">
            {authMode?.local_login_allowed
              ? "Development identity only. Hosted sign-in uses a separate Google OAuth client."
              : authMode?.oidc_configured
                ? "Only the configured owner account can enter."
                : "Owner sign-in is locked until a new Google OAuth client and owner allowlist are configured."}
          </small>
        </div>
        <div className="login-orbit" aria-hidden="true">
          <div />
          <div />
          <div />
          <Aperture size={160} />
        </div>
      </div>
    );
  if (!data)
    return (
      <div className="login">
        <p role="status">Loading workspace…</p>
        {error && <p role="alert">{error}</p>}
        <Button onClick={() => load().catch((e) => setError(e.message))}>
          Retry
        </Button>
      </div>
    );
  const d = data;
  const pending = d.jobs.filter((j) =>
    ["queued", "running", "retry_wait"].includes(j.status),
  );
  const unknown = d.publications.filter((p) => p.state === "unknown");
  const activeOpp =
    d.opportunities.find((o) => o.id === routeId) || d.opportunities[0];
  const activeCampaign =
    d.campaigns.find((c) => c.id === routeId) || d.campaigns[0];
  const exports = filtered(d.exports);
  const currentExport =
    d.exports.find((e) => e.id === (selectedExport || routeId)) || exports[0];
  const title = nav.find((n) => n[0] === section)?.[1] || "Control Room";
  const subtitles: Record<string, string> = {
    "": "Make something worth watching.",
    discover: "Find the story only you can tell.",
    research: "Every factual statement needs a source.",
    campaigns: "Turn verified ideas into original creative direction.",
    assets: "Know what you can use, and why.",
    production: "One idea. Treatments made for each format.",
    review: "Inspect the actual export before you approve it.",
    distribution: "The right story, the right destination.",
    community: "Listen closely. Reply thoughtfully.",
    analytics: "Evidence before conclusions.",
    learning: "Small experiments. Better creative decisions.",
  };
  const defaultAction = (
    <Button onClick={createFixture} disabled={busy}>
      <Sparkles size={16} />
      Create original test story
    </Button>
  );
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (sidebar ? "open" : "")}>
        <Link className="brand" href="/">
          <span className="brand-mark">
            <Play fill="currentColor" size={19} />
          </span>
          <span>
            Screen Central<small>CREATIVE OPERATING SYSTEM</small>
          </span>
        </Link>
        <div className="workspace-label">
          YOUR WORKSPACE <ChevronDown size={13} />
        </div>
        <nav aria-label="Main navigation">
          {nav.map(([slug, label, Icon]) => (
            <Link
              href={"/" + slug}
              key={slug}
              className={section === slug ? "active" : ""}
            >
              <Icon size={18} />
              {label}
              {slug === "review" &&
                d.exports.filter((e) => e.status === "qa_passed").length >
                  0 && (
                  <span className="nav-count">
                    {d.exports.filter((e) => e.status === "qa_passed").length}
                  </span>
                )}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="safe-card">
            <span className="live-dot" />
            {d.environment === "local"
              ? "LOCAL"
              : d.environment.toUpperCase()}{" "}
            SAFE MODE
            <p>
              No live publishing.
              <br />
              No paid provider calls.
            </p>
            <button onClick={() => setOperations(true)}>
              View system status <ArrowRight size={12} />
            </button>
          </div>
          <button className="owner" onClick={() => setOperations(true)}>
            <span className="avatar">SC</span>
            <span>
              Screen Central<small>Owner workspace</small>
            </span>
            <Settings2 size={17} />
          </button>
        </div>
      </aside>
      <main>
        <div className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Toggle navigation"
            onClick={() => setSidebar(!sidebar)}
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <span>{title}</span>
          </div>
          <div className="topbar-right">
            <span className="tiny-status">
              <span className="live-dot" />
              {d.environment === "local"
                ? "LOCAL DEVELOPMENT"
                : d.environment.toUpperCase()}
            </span>
            <button
              className="icon-button"
              aria-label="View needs attention"
              onClick={() => {
                router.push("/");
                setNotice(
                  unknown.length
                    ? `${unknown.length} publication needs reconciliation.`
                    : "No unresolved publication outcomes.",
                );
              }}
            >
              <Bell size={18} />
              {unknown.length > 0 && <span className="notification-dot" />}
            </button>
            <span className="avatar">SC</span>
          </div>
        </div>
        <div className="page">
          <header className="page-header">
            <div>
              <span className="eyebrow">PRIVATE CREATIVE OPERATIONS</span>
              <h1>
                {title}
                <span className="heading-dot">.</span>
              </h1>
              <p>{subtitles[section]}</p>
            </div>
            <div className="header-actions">
              {section === "" ? (
                <>
                  <Button secondary onClick={() => router.push("/campaigns")}>
                    <Clapperboard size={16} />
                    View campaigns
                  </Button>
                  <Button onClick={() => setOpModal(true)}>
                    <Plus size={17} />
                    New idea
                  </Button>
                </>
              ) : (
                <Button
                  secondary
                  onClick={() => {
                    setBusy(true);
                    load()
                      .catch((e) => setError(e.message))
                      .finally(() => setBusy(false));
                  }}
                  disabled={busy}
                >
                  <RefreshCw size={15} className={busy ? "spin" : ""} />
                  Refresh
                </Button>
              )}
            </div>
          </header>
          {error && (
            <div role="alert" className="alert error">
              <TriangleAlert size={19} />
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="alert success">
              <CheckCircle2 size={18} />
              <span>{notice}</span>
              <button
                className="icon-button"
                aria-label="Dismiss notice"
                onClick={() => setNotice("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {section === "" && (
            <>
              <div className="safety-strip">
                <ShieldCheck size={18} />
                <strong>Space to create. Safe by default.</strong>
                <span>
                  Local mock providers · live publishing paused · $0 external
                  spend
                </span>
                <button onClick={() => setOperations(true)}>
                  System status <ArrowRight size={14} />
                </button>
              </div>
              <div className="stats">
                {[
                  [
                    Compass,
                    "Opportunities",
                    d.opportunities.length,
                    "Ideas with potential",
                    "/discover",
                  ],
                  [
                    Clapperboard,
                    "Active campaigns",
                    d.campaigns.length,
                    "Stories in the making",
                    "/campaigns",
                  ],
                  [
                    ShieldCheck,
                    "Ready for review",
                    d.exports.filter((e) => e.status === "qa_passed").length,
                    "Exports awaiting your eye",
                    "/review",
                  ],
                  [
                    AudioLines,
                    "In production",
                    pending.length,
                    "Durable worker jobs",
                    "/production",
                  ],
                ].map(([Icon, label, value, description, href], i) => {
                  const I = Icon as typeof Compass;
                  return (
                    <Link className="stat-card" href={href as string} key={i}>
                      <div>
                        <span>{label as string}</span>
                        <I size={18} />
                      </div>
                      <strong>
                        {value as number}
                        <span>
                          {i === 2 ? "Review queue" : "Local workspace"}
                        </span>
                      </strong>
                      <small>
                        {description as string}
                        <ArrowRight size={14} />
                      </small>
                    </Link>
                  );
                })}
              </div>
              <div className="dashboard-grid">
                <section className="panel feature-panel">
                  <div className="section-top">
                    <span className="mini-label">
                      <Sparkles size={14} />
                      THE NEXT GOOD STORY
                    </span>
                    <span className="outline-pill">ORIGINAL FIXTURE</span>
                  </div>
                  <h2>
                    Great content starts
                    <br />
                    with a better question.
                  </h2>
                  <p>
                    Build a complete fictional campaign, from cited claims to a
                    playable export. Then test distribution without publishing
                    to a real account.
                  </p>
                  <div className="feature-actions">
                    {defaultAction}
                    {link("/discover", "Explore ideas")}
                  </div>
                  <div className="feature-art" aria-hidden="true">
                    <div className="film-ring r1" />
                    <div className="film-ring r2" />
                    <div className="film-ring r3" />
                    <span>
                      <Play size={34} fill="currentColor" />
                    </span>
                    <i className="art-chip">STORY → SCREEN</i>
                  </div>
                  <div className="feature-footer">
                    <span>
                      <Check size={13} />
                      Original test assets
                    </span>
                    <span>
                      <Check size={13} />
                      Evidence attached
                    </span>
                    <span>
                      <Check size={13} />
                      No paid APIs
                    </span>
                  </div>
                </section>
                <section className="panel attention">
                  <div className="section-top">
                    <h2>Needs your attention</h2>
                    <span className="count">
                      {unknown.length +
                        d.claims.filter((c) => c.status !== "supported")
                          .length +
                        d.exports.filter((e) => e.status === "qa_passed")
                          .length}
                    </span>
                  </div>
                  {unknown.length > 0 && (
                    <Link className="attention-item" href="/distribution">
                      <span className="attention-icon amber">
                        <TriangleAlert size={18} />
                      </span>
                      <div>
                        <strong>Unknown mock publication</strong>
                        <p>Reconcile the receipt before another attempt.</p>
                      </div>
                      <ChevronRight size={16} />
                    </Link>
                  )}
                  {d.claims.some((c) => c.status !== "supported") && (
                    <Link className="attention-item" href="/research">
                      <span className="attention-icon amber">
                        <BookOpen size={18} />
                      </span>
                      <div>
                        <strong>Research needs a human review</strong>
                        <p>Inspect exact source passages and identity.</p>
                      </div>
                      <ChevronRight size={16} />
                    </Link>
                  )}
                  {d.exports.some((e) => e.status === "qa_passed") && (
                    <Link className="attention-item" href="/review">
                      <span className="attention-icon mint">
                        <ShieldCheck size={18} />
                      </span>
                      <div>
                        <strong>Exports ready for your review</strong>
                        <p>Watch the media and approve its exact hash.</p>
                      </div>
                      <ChevronRight size={16} />
                    </Link>
                  )}
                  {!unknown.length &&
                    !d.claims.some((c) => c.status !== "supported") &&
                    !d.exports.some((e) => e.status === "qa_passed") && (
                      <div className="attention-clear">
                        <span>
                          <Check size={25} />
                        </span>
                        <h3>A clear runway.</h3>
                        <p>
                          No urgent blockers in your workspace.
                          <br />
                          Your next original story can start here.
                        </p>
                      </div>
                    )}
                  <div className="attention-footer">
                    <span className="live-dot" />
                    Publishing remains paused
                  </div>
                </section>
              </div>
              <section className="panel">
                <div className="section-top">
                  <div>
                    <h2>On the creative desk</h2>
                    <p className="muted small">
                      Your most recent campaigns, from brief to final cut.
                    </p>
                  </div>
                  {link("/campaigns", "All campaigns")}
                </div>
                {!d.campaigns.length ? (
                  <div className="compact-empty">
                    <Clapperboard size={24} />
                    <span>
                      No campaigns yet. Create an idea, verify its research, and
                      bring it to life.
                    </span>
                    {link("/discover", "Get started")}
                  </div>
                ) : (
                  <div className="campaign-table">
                    <div className="table-head">
                      <span>CAMPAIGN</span>
                      <span>FORMATS</span>
                      <span>STATUS</span>
                      <span>CREATED</span>
                    </div>
                    {d.campaigns.slice(0, 4).map((c) => (
                      <Link
                        className="table-row"
                        key={c.id}
                        href={"/campaigns/" + c.id}
                      >
                        <span className="campaign-name">
                          <span className="table-thumb">
                            <Clapperboard size={21} />
                          </span>
                          <span>
                            <strong>{c.title}</strong>
                            <small>{c.series_name}</small>
                          </span>
                        </span>
                        <span className="muted">
                          {
                            d.variants.filter((v) => v.campaign_id === c.id)
                              .length
                          }{" "}
                          native treatments
                        </span>
                        <Badge value={c.status} />
                        <span className="muted small">
                          {time(c.created_at)}
                        </span>
                      </Link>
                    ))}
                  </div>
                )}
              </section>
              <div className="bottom-note">
                <Aperture size={15} />
                <span>Accuracy. Originality. A reason to watch.</span>
                <span>Screen Central OS · Independent local build</span>
              </div>
            </>
          )}
          {section !== "" && (
            <div className="workspace-toolbar">
              <div className="search">
                <Search size={16} />
                <input
                  aria-label="Search workspace"
                  placeholder={"Search " + title.toLowerCase() + "…"}
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <span className="muted small">
                {busy ? (
                  <>
                    <Loader2 size={14} className="spin" /> Saving…
                  </>
                ) : (
                  "Changes saved to PostgreSQL"
                )}
              </span>
            </div>
          )}
          {section === "discover" && (
            <>
              <div className="section-top">
                <h2>Ideas worth investigating</h2>
                <div className="inline-actions">
                  {defaultAction}
                  <Button secondary onClick={() => setOpModal(true)}>
                    <Plus size={16} />
                    Add an idea
                  </Button>
                </div>
              </div>
              {!d.opportunities.length ? (
                <Empty
                  title="Give the next story a starting point"
                  description="Add an original idea or create a fictional fixture to test the complete workflow."
                  action={defaultAction}
                />
              ) : (
                <div className="cards-grid">
                  {filtered(d.opportunities).map((o) => (
                    <article className="panel idea-card" key={o.id}>
                      <div className="section-top">
                        <span className="mini-label">MOMENTS EXPLAINED</span>
                        <Badge value={o.status} />
                      </div>
                      <h2>{o.title}</h2>
                      <p>{o.angle || "Original angle to be researched."}</p>
                      <dl>
                        <dt>Why now?</dt>
                        <dd>{o.rationale?.why_now || "Unknown"}</dd>
                        <dt>Why us?</dt>
                        <dd>{o.why_us || "To be defined"}</dd>
                        <dt>Counterevidence</dt>
                        <dd>
                          {o.rationale?.counterevidence ||
                            "Evidence has not been gathered."}
                        </dd>
                        <dt>Demand / cost to try</dt>
                        <dd>
                          Unknown ·{" "}
                          {o.rationale?.cost_to_try || "Not estimated"}
                        </dd>
                      </dl>
                      <div className="inline-actions">
                        {link("/research/" + o.id, "Open research")}
                        <button
                          className="quiet-button"
                          disabled={busy}
                          onClick={() =>
                            act(
                              "opportunity.decide",
                              o.id,
                              {
                                decision: "deferred",
                                reason: "Owner deferred from discovery",
                              },
                              "Idea deferred with an audit record.",
                            )
                          }
                        >
                          Defer
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
          {section === "research" &&
            (!activeOpp ? (
              <Empty
                title="Start with a question"
                description="Create an opportunity to begin collecting and reviewing evidence."
                action={defaultAction}
              />
            ) : (
              <>
                <div className="selection-row">
                  <label>
                    Research candidate
                    <select
                      aria-label="Research candidate"
                      value={activeOpp.id}
                      onChange={(e) =>
                        router.push("/research/" + e.target.value)
                      }
                    >
                      {d.opportunities.map((o) => (
                        <option value={o.id} key={o.id}>
                          {o.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Badge value={activeOpp.status} />
                </div>
                <div className="section-top">
                  <div>
                    <h2>{activeOpp.title}</h2>
                    <p className="muted">
                      Source text is evidence to inspect. It cannot change app
                      settings or trigger tools.
                    </p>
                  </div>
                  <Button
                    disabled={busy}
                    onClick={() =>
                      act(
                        "research.approve",
                        activeOpp.id,
                        {},
                        "Research package approved and hashed.",
                      )
                    }
                  >
                    <ShieldCheck size={16} />
                    Approve research package
                  </Button>
                </div>
                <div className="research-grid">
                  {filtered(
                    d.claims.filter((c) => c.opportunity_id === activeOpp.id),
                  ).map((c) => (
                    <article className="panel claim-card" key={c.id}>
                      <div className="section-top">
                        <span className="mini-label">
                          ATOMIC CLAIM · REV {c.revision}
                        </span>
                        <Badge value={c.status} />
                      </div>
                      <h3>{c.text}</h3>
                      {d.evidence
                        .filter((e) => e.claim_id === c.id)
                        .map((e) => (
                          <div className="evidence" key={e.id}>
                            <div className="section-top">
                              <strong>{e.source_title}</strong>
                              <Badge value={e.stance} />
                            </div>
                            <blockquote>{e.excerpt}</blockquote>
                            <code>{e.locator}</code>
                            <p className="muted small">
                              Retrieved {time(e.retrieved_at)} ·{" "}
                              {e.reviewed_at
                                ? "Human review recorded"
                                : "Not yet reviewed"}
                            </p>
                            <span className="source-url">{e.uri}</span>
                          </div>
                        ))}
                      {d.claim_blockers?.[c.id]?.map((b: string) => (
                        <p className="blocker" key={b}>
                          <TriangleAlert size={14} />
                          {b}
                        </p>
                      ))}
                      <label className="check-label">
                        <input
                          type="checkbox"
                          checked={!!c.factual_value?.identity_resolved}
                          readOnly
                        />
                        Canonical identity{" "}
                        {c.factual_value?.identity_resolved
                          ? "resolved"
                          : "requires review"}
                      </label>
                      <Button
                        secondary
                        disabled={busy}
                        onClick={() =>
                          act(
                            "claim.review",
                            c.id,
                            {
                              expected_revision: c.revision,
                              review_note:
                                reviewNote ||
                                "Inspected exact supporting passage and canonical fixture identity.",
                              resolve_identity: true,
                            },
                            "Claim adjudicated. Downstream approvals were rechecked.",
                          )
                        }
                      >
                        <Check size={16} />
                        Review exact evidence
                      </Button>
                    </article>
                  ))}
                </div>
                <div className="panel form-panel">
                  <h3>Review note</h3>
                  <label>
                    Record what you inspected
                    <input
                      value={reviewNote}
                      onChange={(e) => setReviewNote(e.target.value)}
                      placeholder="Exact source passage, identity, and any remaining uncertainty"
                    />
                  </label>
                  <div className="inline-actions">
                    <Button
                      disabled={busy}
                      onClick={async () => {
                        const r = await act(
                          "campaign.create",
                          activeOpp.id,
                          {},
                          "Campaign and three independent format drafts created.",
                        );
                        if (r) router.push("/campaigns/" + r.id);
                      }}
                    >
                      <Clapperboard size={16} />
                      Create campaign from approved research
                    </Button>
                  </div>
                </div>
                <details className="panel">
                  <summary>Add source excerpt and claim</summary>
                  <form
                    className="form-grid"
                    onSubmit={async (e) => {
                      e.preventDefault();
                      const f = new FormData(e.currentTarget);
                      await act(
                        "source.attach",
                        activeOpp.id,
                        Object.fromEntries(f),
                        "Source excerpt attached. Identity and evidence still need human review.",
                      );
                    }}
                  >
                    <label>
                      Source title
                      <input name="title" required />
                    </label>
                    <label>
                      HTTPS reference URL
                      <input
                        name="url"
                        type="url"
                        required
                        placeholder="https://…"
                      />
                    </label>
                    <label>
                      Exact permitted excerpt
                      <textarea
                        name="excerpt"
                        minLength={10}
                        maxLength={4000}
                        required
                      />
                    </label>
                    <label>
                      Atomic factual claim
                      <input name="claim" required />
                    </label>
                    <label>
                      Passage locator
                      <input
                        name="locator"
                        required
                        placeholder="Paragraph 3, sentence 1"
                      />
                    </label>
                    <button className="button" disabled={busy}>
                      Attach for review
                    </button>
                  </form>
                </details>
              </>
            ))}
          {section === "campaigns" &&
            (!activeCampaign ? (
              <Empty
                title="Every campaign starts with verified research"
                description="Review a candidate and approve its research package to create three native format drafts."
                action={
                  <Button onClick={() => router.push("/research")}>
                    <BookOpen size={16} />
                    Go to Research Desk
                  </Button>
                }
              />
            ) : (
              <>
                <label className="selection-label">
                  Campaign
                  <select
                    value={activeCampaign.id}
                    onChange={(e) =>
                      router.push("/campaigns/" + e.target.value)
                    }
                  >
                    {d.campaigns.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.title}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="panel campaign-brief">
                  <div>
                    <span className="mini-label">
                      {activeCampaign.series_name}
                    </span>
                    <h2>{activeCampaign.title}</h2>
                    <p>{activeCampaign.viewer_promise}</p>
                    <p className="muted">
                      Original angle: {activeCampaign.original_angle}
                    </p>
                  </div>
                  <Badge value={activeCampaign.status} />
                </div>
                {filtered(
                  d.variants.filter((v) => v.campaign_id === activeCampaign.id),
                ).map((v) => {
                  const s = d.scripts.find((s) => s.variant_id === v.id);
                  if (!s) return null;
                  return (
                    <section className="panel variant-editor" key={v.id}>
                      <div className="section-top">
                        <div>
                          <h2>{formatName(v.format)}</h2>
                          <p className="muted">{v.angle}</p>
                        </div>
                        <Badge value={s.review_status} />
                      </div>
                      <label>
                        Approved source image
                        <select
                          aria-label={"Source image " + v.format}
                          value={
                            d.asset_usage?.find(
                              (a: Row) => a.variant_id === v.id,
                            )?.asset_id || ""
                          }
                          onChange={(e) =>
                            act(
                              "variant.select_asset",
                              v.id,
                              { asset_id: e.target.value },
                              "Image selected. Reapprove the script and render to inspect the new inputs.",
                            )
                          }
                        >
                          <option value="">
                            Select a rights-cleared image
                          </option>
                          {d.assets
                            .filter((a) => a.status === "approved")
                            .map((a) => (
                              <option key={a.id} value={a.id}>
                                {a.filename}
                              </option>
                            ))}
                        </select>
                      </label>
                      <div className="script-lines">
                        {s.sentences.map((line: any, i: number) => (
                          <div key={line.sentence_id}>
                            <span className="line-number">
                              {String(i + 1).padStart(2, "0")}
                            </span>
                            <div>
                              <strong>{line.text}</strong>
                              <small>
                                <Badge value={line.kind} />
                                {line.claim_refs?.length
                                  ? line.claim_refs.map((id: string) => (
                                      <code key={id}>
                                        claim {shortHash(id)}
                                      </code>
                                    ))
                                  : "Editorial interpretation · no factual assertion"}
                              </small>
                            </div>
                          </div>
                        ))}
                      </div>
                      <details>
                        <summary>
                          Edit this script · revision {s.revision}
                        </summary>
                        <p className="muted small">
                          One sentence per line. Factual lines retain citations
                          and must exactly match their approved atomic claim in
                          this initial renderer.
                        </p>
                        <textarea
                          aria-label={"Script " + v.format}
                          value={
                            scriptText[v.id] ??
                            s.sentences.map((l: any) => l.text).join("\n")
                          }
                          onChange={(e) =>
                            setScriptText({
                              ...scriptText,
                              [v.id]: e.target.value,
                            })
                          }
                        />
                        <Button
                          secondary
                          disabled={busy}
                          onClick={() => {
                            const lines = (
                              scriptText[v.id] ??
                              s.sentences.map((l: any) => l.text).join("\n")
                            )
                              .split("\n")
                              .filter(Boolean);
                            act(
                              "script.save",
                              v.id,
                              {
                                expected_revision: s.revision,
                                sentences: lines.map(
                                  (text: string, i: number) => ({
                                    ...s.sentences[i],
                                    sentence_id: "s" + (i + 1),
                                    text,
                                    kind: s.sentences[i]?.kind || "factual",
                                    claim_refs:
                                      s.sentences[i]?.claim_refs || [],
                                  }),
                                ),
                              },
                              "New script revision saved. Earlier export approvals were revoked.",
                            );
                          }}
                        >
                          Save new revision
                        </Button>
                      </details>
                      <div className="variant-footer">
                        <code>SHA-256 {shortHash(s.text_sha256)}</code>
                        <div className="inline-actions">
                          <Button
                            secondary
                            disabled={
                              busy || s.review_status === "owner_approved"
                            }
                            onClick={() =>
                              act(
                                "script.approve",
                                v.id,
                                {
                                  expected_revision: s.revision,
                                  expected_hash: s.text_sha256,
                                },
                                "Exact script approved after deterministic claim and rights checks.",
                              )
                            }
                          >
                            <Check size={15} />
                            Approve script
                          </Button>
                          <Button
                            disabled={
                              busy || s.review_status !== "owner_approved"
                            }
                            onClick={async () => {
                              const r = await act(
                                "render",
                                v.id,
                                {},
                                "Render queued for the separate media worker.",
                              );
                              if (r)
                                router.push("/production/" + activeCampaign.id);
                            }}
                          >
                            <Play size={15} />
                            Render{" "}
                            {v.format === "carousel_4_5" ? "carousel" : "video"}
                          </Button>
                        </div>
                      </div>
                    </section>
                  );
                })}
              </>
            ))}
          {section === "assets" && (
            <>
              <details className="panel">
                <summary>Upload an owned image</summary>
                <p className="muted small">
                  PNG, JPEG or WebP · up to 8 MB / 20 megapixels · stored
                  privately, with rights pending.
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    uploadImage(e.currentTarget);
                  }}
                >
                  <label>
                    Select image
                    <input
                      name="file"
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      required
                    />
                  </label>
                  <button className="button" disabled={busy}>
                    Upload for rights review
                  </button>
                </form>
              </details>
              {!d.assets.length ? (
                <Empty
                  title="An original library starts here"
                  description="The local fixture creates original geometric artwork and a separate rights record."
                  action={defaultAction}
                />
              ) : (
                <div className="cards-grid">
                  {filtered(d.assets).map((a) => (
                    <article className="panel asset-card" key={a.id}>
                      <img
                        src={"/api/v1/assets/" + a.id + "/view"}
                        alt="Original geometric lighthouse fixture"
                      />
                      <div className="asset-body">
                        <div className="section-top">
                          <h3>{a.filename}</h3>
                          <Badge value={a.status} />
                        </div>
                        <p className="muted">
                          {a.width} × {a.height} ·{" "}
                          {(a.byte_size / 1024).toFixed(0)} KB · {a.origin_type}
                        </p>
                        {d.rights
                          .filter((r) => r.asset_id === a.id)
                          .map((r) => (
                            <dl key={r.id}>
                              <dt>Usage basis</dt>
                              <dd>
                                {r.rights_kind} · derivative use{" "}
                                {r.derivatives_allowed
                                  ? "permitted"
                                  : "blocked"}
                              </dd>
                              <dt>Platforms</dt>
                              <dd>{r.platforms.join(", ")}</dd>
                              <dt>Rights review</dt>
                              <dd>{r.notes}</dd>
                            </dl>
                          ))}
                        <code>SHA-256 {shortHash(a.sha256)}</code>
                        {a.status === "quarantine" && (
                          <form
                            onSubmit={(e) => {
                              e.preventDefault();
                              const f = new FormData(e.currentTarget);
                              act(
                                "asset.review_rights",
                                a.id,
                                {
                                  owner_attestation: f.get("attest") === "on",
                                  review_note: f.get("note"),
                                },
                                "Ownership attestation saved. Image is eligible for local render use.",
                              );
                            }}
                          >
                            <label>
                              Specific ownership basis
                              <textarea
                                name="note"
                                required
                                minLength={15}
                                placeholder="Who created this image? What use is permitted?"
                              />
                            </label>
                            <label className="check-label">
                              <input name="attest" type="checkbox" required />I
                              own this image and permit derivatives for the
                              selected test platforms.
                            </label>
                            <button className="button" disabled={busy}>
                              Record rights review
                            </button>
                          </form>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
          {section === "production" && (
            <>
              <div className="section-top">
                <h2>Production queue</h2>
                {link("/campaigns", "Scripts & treatments")}
              </div>
              {!d.jobs.length ? (
                <Empty
                  title="Ready when your script is"
                  description="Approve a format-specific script in Campaign Studio, then send it to the media worker."
                  action={
                    <Button onClick={() => router.push("/campaigns")}>
                      Open Campaign Studio
                      <ArrowRight size={16} />
                    </Button>
                  }
                />
              ) : (
                <div className="panel">
                  {filtered(d.jobs).map((j) => (
                    <div className="job-row" key={j.id}>
                      <span className="job-icon">
                        {j.status === "running" ? (
                          <Loader2 className="spin" />
                        ) : j.status === "succeeded" ? (
                          <CheckCircle2 />
                        ) : (
                          <Clapperboard />
                        )}
                      </span>
                      <div>
                        <strong>
                          {j.kind === "render"
                            ? formatName(
                                d.variants.find((v) => v.id === j.aggregate_id)
                                  ?.format || "Media render",
                              )
                            : "Mock publication"}
                        </strong>
                        <p className="muted small">
                          Job {shortHash(j.id)} · attempt {j.attempt_count}/
                          {j.max_attempts} · lease epoch {j.lease_epoch}
                        </p>
                        {j.last_error_summary && (
                          <p className="blocker">
                            {j.last_error_code}: {j.last_error_summary}
                          </p>
                        )}
                      </div>
                      <Badge value={j.status} />
                      {j.output?.export_id &&
                        link("/review/" + j.output.export_id, "Inspect export")}
                      {j.status === "queued" && (
                        <button
                          className="quiet-button"
                          onClick={() => act("job.cancel", j.id)}
                          disabled={busy}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className="section-top">
                <h2>Rendered media</h2>
                <span className="muted small">
                  Immutable files · actual local outputs
                </span>
              </div>
              <div className="cards-grid">
                {exports.map((ex) => (
                  <article className="panel export-card" key={ex.id}>
                    <img
                      src={
                        "/api/v1/exports/" + ex.id + "/preview?artifact=poster"
                      }
                      alt={formatName(ex.format) + " export poster"}
                    />
                    <div className="asset-body">
                      <div className="section-top">
                        <h3>{formatName(ex.format)}</h3>
                        <Badge value={ex.status} />
                      </div>
                      <p className="muted small">
                        {ex.width} × {ex.height} ·{" "}
                        {ex.duration_ms
                          ? ex.duration_ms / 1000 + " seconds"
                          : "3 original cards"}
                      </p>
                      {link("/review/" + ex.id, "Play & inspect")}
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
          {section === "review" &&
            (!currentExport ? (
              <Empty
                title="The final cut deserves a close look"
                description="Render an approved script to inspect the actual file, technical checks, and immutable export hash."
                action={
                  <Button onClick={() => router.push("/campaigns")}>
                    Open Campaign Studio
                    <ArrowRight size={16} />
                  </Button>
                }
              />
            ) : (
              <>
                <label className="selection-label">
                  Export
                  <select
                    value={currentExport.id}
                    onChange={(e) => {
                      setSelectedExport(e.target.value);
                      router.push("/review/" + e.target.value);
                    }}
                  >
                    {d.exports.map((e) => (
                      <option key={e.id} value={e.id}>
                        {formatName(e.format)} · {shortHash(e.sha256)} ·{" "}
                        {e.status}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="review-grid">
                  <section className="panel preview-panel">
                    <div className="section-top">
                      <h2>{formatName(currentExport.format)}</h2>
                      <Badge value={currentExport.status} />
                    </div>
                    {currentExport.format === "carousel_4_5" ? (
                      <div className="carousel-preview">
                        {currentExport.codec.slides.map((s: any, i: number) => (
                          <img
                            key={s.key}
                            src={
                              "/api/v1/exports/" +
                              currentExport.id +
                              "/preview?artifact=slide&slide=" +
                              i
                            }
                            alt={s.alt}
                          />
                        ))}
                      </div>
                    ) : (
                      <video
                        key={currentExport.id}
                        controls
                        preload="metadata"
                        poster={
                          "/api/v1/exports/" +
                          currentExport.id +
                          "/preview?artifact=poster"
                        }
                        src={"/api/v1/exports/" + currentExport.id + "/preview"}
                        aria-label="Final export preview"
                      />
                    )}
                    <div className="media-meta">
                      <span>
                        {currentExport.width} × {currentExport.height}
                      </span>
                      <span>
                        {(currentExport.byte_size / 1024 / 1024).toFixed(2)} MB
                      </span>
                      <span>Original synthetic test material</span>
                    </div>
                    <a
                      className="text-link"
                      href={"/api/v1/exports/" + currentExport.id + "/preview"}
                      download
                    >
                      <ArrowDownToLine size={15} />
                      Download exact export
                    </a>
                  </section>
                  <section className="panel qa-panel">
                    <h2>Export inspection</h2>
                    <p className="muted small">
                      Technical checks support your editorial review.
                    </p>
                    {d.quality
                      .filter((q) => q.export_id === currentExport.id)
                      .map((q) => (
                        <details className="qa-check" key={q.id}>
                          <summary>
                            {q.status === "pass" ? (
                              <CheckCircle2 size={17} />
                            ) : (
                              <TriangleAlert size={17} />
                            )}
                            <span>{q.check_name.replaceAll("_", " ")}</span>
                            <Badge value={q.status} />
                          </summary>
                          <pre>{JSON.stringify(q.observed_value, null, 2)}</pre>
                        </details>
                      ))}
                    <div className="hash-box">
                      <span className="mini-label">
                        IMMUTABLE EXPORT · SHA-256
                      </span>
                      <code>{currentExport.sha256}</code>
                      <span className="mini-label">INPUT SNAPSHOT</span>
                      <code>{currentExport.input_snapshot_hash}</code>
                    </div>
                    <label>
                      Editorial & rights review note
                      <textarea
                        placeholder="What did you inspect? Record any limitations."
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                      />
                    </label>
                    <Button
                      disabled={
                        busy ||
                        reviewNote.length < 3 ||
                        currentExport.status === "revoked"
                      }
                      onClick={() =>
                        act(
                          "export.approve",
                          currentExport.id,
                          {
                            expected_hash: currentExport.sha256,
                            review_note: reviewNote,
                          },
                          "Approval recorded for this exact export hash and input snapshot.",
                        )
                      }
                    >
                      <ShieldCheck size={16} />
                      Approve exact export
                    </Button>
                    {currentExport.status === "approved" && (
                      <>
                        <Button
                          secondary
                          onClick={() => {
                            setPackageExport(currentExport.id);
                            router.push("/distribution");
                          }}
                        >
                          Prepare distribution
                          <ArrowRight size={16} />
                        </Button>
                        <button
                          className="quiet-button"
                          onClick={() =>
                            act(
                              "export.revoke",
                              currentExport.id,
                              {},
                              "Export and dependent packages revoked.",
                            )
                          }
                        >
                          Revoke approval
                        </button>
                      </>
                    )}
                  </section>
                </div>
              </>
            ))}
          {section === "distribution" && (
            <>
              <div className="safety-strip">
                <ShieldOff size={18} />
                <strong>Live publishing is paused.</strong>
                <span>
                  Only mock accounts can receive local simulation intents.
                </span>
              </div>
              <div className="distribution-grid">
                <section className="panel form-panel">
                  <div className="section-top">
                    <h2>Prepare a destination package</h2>
                    <Badge value="mock" />
                  </div>
                  <label>
                    Approved export
                    <select
                      value={packageExport}
                      onChange={(e) => setPackageExport(e.target.value)}
                    >
                      <option value="">Select an approved export</option>
                      {d.exports
                        .filter((e) => e.status === "approved")
                        .map((e) => (
                          <option key={e.id} value={e.id}>
                            {formatName(e.format)} · {shortHash(e.sha256)}
                          </option>
                        ))}
                    </select>
                  </label>
                  <label>
                    Exact destination account
                    <select
                      value={accountId}
                      onChange={(e) => setAccountId(e.target.value)}
                    >
                      <option value="">Select a mock account</option>
                      {d["social/accounts"].map((a: Row) => (
                        <option key={a.id} value={a.id}>
                          {a.platform} · {a.external_account_id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Platform title
                    <input
                      value={packageTitle}
                      maxLength={100}
                      onChange={(e) => setPackageTitle(e.target.value)}
                      placeholder="Use the campaign title, or write a destination-specific title"
                    />
                  </label>
                  <label>
                    Platform caption
                    <textarea
                      value={caption}
                      onChange={(e) => setCaption(e.target.value)}
                      maxLength={5000}
                    />
                  </label>
                  <Button
                    disabled={busy || !packageExport || !accountId}
                    onClick={() =>
                      act(
                        "package.create",
                        packageExport,
                        {
                          account_id: accountId,
                          caption,
                          title:
                            packageTitle ||
                            (
                              d.campaigns.find(
                                (c) =>
                                  c.id ===
                                  d.variants.find(
                                    (v) =>
                                      v.id ===
                                      d.exports.find(
                                        (e) => e.id === packageExport,
                                      )?.variant_id,
                                  )?.campaign_id,
                              )?.title || "Screen Central original"
                            ).slice(0, 100),
                        },
                        "Exact destination package validated and approved for local mock use.",
                      )
                    }
                  >
                    <Plus size={15} />
                    Create mock package
                  </Button>
                </section>
                <section className="panel">
                  <h2>Destination accounts</h2>
                  <p className="muted small">
                    Real accounts require separate authorization.
                  </p>
                  {d["social/accounts"].map((a: Row) => (
                    <div className="account-row" key={a.id}>
                      <span className={"platform-icon " + a.platform}>
                        <Play size={16} />
                      </span>
                      <div>
                        <strong>{a.platform}</strong>
                        <code>{a.external_account_id}</code>
                        <small>
                          Mock adapter · real publishing unavailable
                        </small>
                      </div>
                      <Badge value="mock" />
                    </div>
                  ))}
                </section>
              </div>
              <div className="section-top">
                <h2>Platform packages</h2>
                <span className="muted small">
                  Approval binds the export and destination account.
                </span>
              </div>
              <label className="selection-label">
                Optional mock schedule · America/New_York
                <input
                  type="datetime-local"
                  value={schedule}
                  onChange={(e) => setSchedule(e.target.value)}
                />
              </label>
              <label className="check-label">
                <input
                  type="checkbox"
                  checked={lostResponse}
                  onChange={(e) => setLostResponse(e.target.checked)}
                />
                Simulate acknowledgment lost after mock provider acceptance
              </label>
              {d["social/packages"].length === 0 ? (
                <div className="compact-empty">
                  Approve an export, then create a platform package above.
                </div>
              ) : (
                filtered(d["social/packages"]).map((p: Row) => {
                  const a = d["social/accounts"].find(
                    (a: Row) => a.id === p.account_id,
                  );
                  return (
                    <article className="panel package-row" key={p.id}>
                      <div>
                        <div className="section-top">
                          <h3>{p.title}</h3>
                          <Badge value={p.status} />
                        </div>
                        <p>{p.caption}</p>
                        <code>
                          {a?.external_account_id} · package{" "}
                          {shortHash(p.content_hash)}
                        </code>
                      </div>
                      <Button
                        disabled={busy || p.status !== "approved"}
                        onClick={() =>
                          act(
                            "publish.mock",
                            p.id,
                            {
                              external_account_id: a?.external_account_id,
                              simulate_response_lost: lostResponse,
                              scheduled_at: schedule
                                ? new Date(schedule).toISOString()
                                : null,
                            },
                            "Mock submission scheduled. No external platform will be contacted.",
                          )
                        }
                      >
                        <Send size={15} />
                        Schedule mock submit
                      </Button>
                    </article>
                  );
                })
              )}
              <div className="section-top">
                <h2>Publication journal</h2>
                <span className="muted small">
                  One unresolved attempt per export and account.
                </span>
              </div>
              {filtered(d.publications).map((p) => (
                <article className="panel publication-row" key={p.id}>
                  <div>
                    <div className="inline-actions">
                      <Badge value={p.state} />
                      <code>{shortHash(p.id)}</code>
                    </div>
                    <p className="muted small">
                      {
                        d["social/accounts"].find(
                          (a: Row) => a.id === p.account_id,
                        )?.external_account_id
                      }{" "}
                      · {p.not_before && time(p.not_before)}
                    </p>
                    {p.external_post_id && <code>{p.external_post_id}</code>}
                    {p.state === "unknown" && (
                      <p className="blocker">
                        The mock provider may have accepted this. Submission is
                        held until receipt reconciliation.
                      </p>
                    )}
                  </div>
                  {p.state === "unknown" && (
                    <Button
                      disabled={busy}
                      secondary
                      onClick={() =>
                        act(
                          "publish.reconcile",
                          p.id,
                          {},
                          "Provider receipt reconciled. Confirmed with one mock submission; no retry performed.",
                        )
                      }
                    >
                      <RefreshCw size={15} />
                      Reconcile receipt
                    </Button>
                  )}
                </article>
              ))}
            </>
          )}
          {section === "community" && (
            <>
              <div className="section-top">
                <h2>Conversations worth having</h2>
                <Button
                  secondary
                  disabled={busy}
                  onClick={() =>
                    act(
                      "community.fixture",
                      null,
                      {},
                      "Three deidentified synthetic comments imported. No live account was read.",
                    )
                  }
                >
                  <ArrowDownToLine size={15} />
                  Import test comments
                </Button>
              </div>
              {!d["community/threads"].length ? (
                <Empty
                  title="Listen before you respond"
                  description="Import synthetic comments to test drafts, exact-text approvals, and mock replies."
                />
              ) : (
                filtered(d["community/threads"]).map((t) => (
                  <article className="panel comment-card" key={t.id}>
                    <div className="section-top">
                      <span className="mini-label">
                        SYNTHETIC VIEWER · YOUTUBE MOCK
                      </span>
                      <Badge value={t.category} />
                    </div>
                    <h3>{t.summary}</h3>
                    <p className="muted small">
                      {t.topic} · {time(t.first_seen_at)}
                    </p>
                    {t.status !== "deleted" && (
                      <>
                        <label>
                          Write an individual reply
                          <textarea
                            value={replyTexts[t.id] || ""}
                            onChange={(e) =>
                              setReplyTexts({
                                ...replyTexts,
                                [t.id]: e.target.value,
                              })
                            }
                            placeholder="A specific, thoughtful reply for this comment"
                          />
                        </label>
                        <div className="inline-actions">
                          <Button
                            secondary
                            disabled={busy || !replyTexts[t.id]}
                            onClick={() =>
                              act(
                                "reply.save",
                                t.id,
                                { text: replyTexts[t.id] },
                                "Reply saved as a draft; not sent.",
                              )
                            }
                          >
                            <MessageSquare size={15} />
                            Save draft
                          </Button>
                          <button
                            className="quiet-button"
                            onClick={() =>
                              act(
                                "comment.delete",
                                t.id,
                                {},
                                "Comment text and stored reply text removed from the local workspace.",
                              )
                            }
                          >
                            Remove comment data
                          </button>
                        </div>
                      </>
                    )}
                    {d.replies
                      .filter((r) => r.thread_id === t.id)
                      .map((r) => (
                        <div className="reply" key={r.id}>
                          <div className="section-top">
                            <p>{r.draft_text}</p>
                            <Badge value={r.state} />
                          </div>
                          <code>Exact text {shortHash(r.draft_hash)}</code>
                          <div className="inline-actions">
                            {r.state === "draft" && (
                              <Button
                                secondary
                                disabled={busy}
                                onClick={() =>
                                  act(
                                    "reply.approve",
                                    r.id,
                                    { expected_hash: r.draft_hash },
                                    "Exact reply text approved for this comment.",
                                  )
                                }
                              >
                                Approve exact text
                              </Button>
                            )}
                            {r.state === "approved" && (
                              <Button
                                disabled={busy}
                                onClick={() =>
                                  act(
                                    "reply.send_mock",
                                    r.id,
                                    { expected_hash: r.draft_hash },
                                    "Individual mock reply confirmed. No public reply sent.",
                                  )
                                }
                              >
                                <Send size={14} />
                                Send mock reply
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                  </article>
                ))
              )}
            </>
          )}
          {section === "analytics" && (
            <>
              <div className="section-top">
                <div>
                  <h2>Performance with context</h2>
                  <p className="muted">
                    Separate platforms. Comparable windows. Honest gaps.
                  </p>
                </div>
                <Button
                  secondary
                  disabled={busy}
                  onClick={() =>
                    act(
                      "analytics.fixture",
                      null,
                      {},
                      "Synthetic 48-hour observations imported. These are not real channel metrics.",
                    )
                  }
                >
                  <ArrowDownToLine size={15} />
                  Import synthetic observations
                </Button>
              </div>
              <div className="alert info">
                <FlaskConical size={19} />
                <span>
                  All current observations are synthetic test data. Missing
                  values remain unknown.
                </span>
              </div>
              {!d["analytics/observations"].length ? (
                <Empty
                  title="Evidence will appear here"
                  description="Import the fixture to inspect metric provenance and missing-data behavior."
                />
              ) : (
                <div className="cards-grid">
                  {d["social/accounts"].map((a: Row) => (
                    <section className="panel metric-panel" key={a.id}>
                      <div className="section-top">
                        <h2 className="capitalize">{a.platform}</h2>
                        <Badge value="mock">SYNTHETIC</Badge>
                      </div>
                      <p className="muted small">
                        Short · first 48 hours · n = 1
                      </p>
                      {d["analytics/observations"]
                        .filter((o: Row) => o.account_id === a.id)
                        .map((o: Row) => (
                          <div className="metric-line" key={o.id}>
                            <span>{o.metric.replaceAll("_", " ")}</span>
                            <strong>
                              {o.value === null
                                ? "Unknown"
                                : Number(o.value).toLocaleString()}
                            </strong>
                            {o.missing_reason && (
                              <small>{o.missing_reason}</small>
                            )}
                          </div>
                        ))}
                      <div className="mini-bars" aria-hidden="true">
                        {[20, 40, 30, 65, 45, 80, 70, 90, 60, 85, 75, 100].map(
                          (n, i) => (
                            <i key={i} style={{ height: n + "%" }} />
                          ),
                        )}
                      </div>
                      <small className="muted">
                        Illustrative fixture bars · not an observed time series
                      </small>
                      <p className="muted small">
                        Source: synthetic_fixture
                        <br />
                        Retention unavailable · sample too small for a
                        conclusion
                      </p>
                    </section>
                  ))}
                </div>
              )}
            </>
          )}
          {section === "learning" && (
            <>
              <div className="panel learning-intro">
                <FlaskConical size={26} />
                <div>
                  <span className="mini-label">
                    A HYPOTHESIS IS A STARTING POINT
                  </span>
                  <h2>Make the next test smaller and clearer.</h2>
                  <p>
                    Current evidence is synthetic and insufficient for a real
                    channel recommendation. Register what you expect before
                    collecting results.
                  </p>
                </div>
                <Badge value="uncertain">INCONCLUSIVE</Badge>
              </div>
              <div className="distribution-grid">
                <section className="panel form-panel">
                  <h2>Pre-register an experiment</h2>
                  <form
                    onSubmit={async (e) => {
                      e.preventDefault();
                      const f = new FormData(e.currentTarget);
                      await act(
                        "experiment.create",
                        null,
                        Object.fromEntries(f),
                        "Experiment protocol registered before results are available.",
                      );
                    }}
                  >
                    <label>
                      Experiment name
                      <input
                        name="name"
                        required
                        placeholder="Immediate visual promise"
                      />
                    </label>
                    <label>
                      Hypothesis
                      <textarea
                        name="hypothesis"
                        minLength={10}
                        required
                        placeholder="A specific opening image may improve average view duration at 48 hours."
                      />
                    </label>
                    <label>
                      Success / stop criterion
                      <input
                        name="success_criterion"
                        required
                        placeholder="Compare mature same-format cohorts; stop if clarity falls."
                      />
                    </label>
                    <button className="button" disabled={busy}>
                      <Plus size={15} />
                      Register experiment
                    </button>
                  </form>
                </section>
                <section className="panel">
                  <h2>Evidence gaps</h2>
                  {[
                    "No authenticated channel observations",
                    "Retention not available in the fixture",
                    "One synthetic item per platform",
                    "Topic and timing can confound a comparison",
                  ].map((s) => (
                    <div className="gap" key={s}>
                      <TriangleAlert size={16} />
                      {s}
                    </div>
                  ))}
                  <p className="muted small">
                    No causal conclusion. No automatic change to publishing or
                    editorial rules.
                  </p>
                </section>
              </div>
              {filtered(d.experiments).map((ex) => (
                <section className="panel" key={ex.id}>
                  <div className="section-top">
                    <h2>{ex.name}</h2>
                    <Badge value={ex.state} />
                  </div>
                  <p>{ex.hypothesis}</p>
                  <p className="muted">
                    Primary metric: {ex.primary_metric} · YouTube Short · first
                    48 hours
                  </p>
                  <p>{ex.success_criterion}</p>
                  <p className="blocker">{ex.confidence_note}</p>
                  <span className="muted small">
                    Pre-registered {time(ex.pre_registered_at)} · protocol{" "}
                    {ex.protocol_version}
                  </span>
                </section>
              ))}
            </>
          )}
        </div>
      </main>
      {opModal && (
        <div className="modal-backdrop" onClick={() => setOpModal(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="idea-title"
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="section-top">
              <h2 id="idea-title">Start with an original idea</h2>
              <button
                className="icon-button"
                aria-label="Close new idea"
                onClick={() => setOpModal(false)}
              >
                <X />
              </button>
            </div>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                const r = await act(
                  "opportunity.create",
                  null,
                  Object.fromEntries(f),
                  "Idea saved. Gather evidence in Research Desk.",
                );
                if (r) {
                  setOpModal(false);
                  router.push("/research/" + r.id);
                }
              }}
            >
              <label>
                Working title
                <input
                  name="title"
                  autoFocus
                  required
                  minLength={5}
                  placeholder="What is the question worth answering?"
                />
              </label>
              <label>
                Original angle
                <textarea
                  name="angle"
                  placeholder="The specific perspective you can bring"
                />
              </label>
              <label>
                Audience hypothesis
                <input
                  name="audience_hypothesis"
                  required
                  placeholder="Who will care, and why?"
                />
              </label>
              <label>
                Why Screen Central?
                <input name="why_us" required />
              </label>
              <button className="button" disabled={busy}>
                <Plus size={16} />
                Create idea
              </button>
            </form>
          </section>
        </div>
      )}
      {operations && (
        <div className="modal-backdrop" onClick={() => setOperations(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="system-title"
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="section-top">
              <h2 id="system-title">System status</h2>
              <button
                className="icon-button"
                aria-label="Close system status"
                onClick={() => setOperations(false)}
              >
                <X />
              </button>
            </div>
            <div className="system-items">
              {[
                [
                  "Environment",
                  d.environment === "local"
                    ? "Local development"
                    : d.environment,
                ],
                ["Database", "PostgreSQL · isolated SCOS database"],
                [
                  "Object storage",
                  d.environment === "local"
                    ? "Private local S3 emulator"
                    : d.data_provider === "supabase"
                      ? "Private Supabase Storage"
                      : "Private S3 storage",
                ],
                [
                  "Media worker",
                  pending.length
                    ? pending.length + " active / queued jobs"
                    : "Idle · polling durable queue",
                ],
                ["Live publishing", "Disabled · no live adapter"],
                [
                  "AI provider",
                  d.ai_provider === "gemini"
                    ? "Gemini · paid calls disabled"
                    : "Local fixtures · $0 external calls",
                ],
                [
                  "Authentication",
                  d.environment === "local"
                    ? "Local development fixture"
                    : "Owner-only Google OIDC",
                ],
              ].map(([k, v]) => (
                <div key={k}>
                  <span>{k}</span>
                  <strong>{v}</strong>
                </div>
              ))}
            </div>
            <details>
              <summary>Recent audit activity</summary>
              {d["audit-events"].slice(0, 12).map((e: Row) => (
                <p className="muted small" key={e.id}>
                  {e.action} · {time(e.created_at)}
                </p>
              ))}
            </details>
            <Button
              secondary
              onClick={async () => {
                await fetch("/api/v1/auth/logout", {
                  method: "POST",
                  headers: { "X-CSRF-Token": csrf },
                });
                setSigned(false);
                setData(null);
                setOperations(false);
              }}
            >
              <LogOut size={16} />
              Sign out
            </Button>
          </section>
        </div>
      )}
    </div>
  );
}
