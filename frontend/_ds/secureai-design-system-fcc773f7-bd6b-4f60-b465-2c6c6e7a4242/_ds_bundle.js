/* @ds-bundle: {"format":3,"namespace":"SecureAIDesignSystem_fcc773","components":[],"sourceHashes":{"ui_kits/editor/AppHeader.jsx":"1ddae84995dd","ui_kits/editor/AppSidebar.jsx":"cec7d453c6e2","ui_kits/editor/Dashboard.jsx":"93b6213378c6","ui_kits/editor/EditorPanel.jsx":"be40ff92b636","ui_kits/editor/RightPanel.jsx":"12f6511a6446","ui_kits/editor/Shared.jsx":"8dea5df25881"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.SecureAIDesignSystem_fcc773 = window.SecureAIDesignSystem_fcc773 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/editor/AppHeader.jsx
try { (() => {
// SecureAI — AppHeader component
const {
  useState
} = React;
function AppHeader({
  viewMode,
  setViewMode,
  severityFilter,
  setSeverityFilter,
  isAnalyzing,
  startAnalysis,
  sidebarOpen,
  setSidebarOpen
}) {
  const SEV_FILTERS = ['critical', 'high', 'medium', 'low'];
  const SEV_COLORS = {
    critical: '#f04141',
    high: '#f59e0b',
    medium: '#eab308',
    low: '#22c55e'
  };
  return /*#__PURE__*/React.createElement("header", {
    style: {
      height: 48,
      flexShrink: 0,
      background: DS.colors.bg1,
      borderBottom: `1px solid ${DS.colors.border}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      gap: 12,
      zIndex: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setSidebarOpen(v => !v),
    style: {
      background: 'none',
      border: 'none',
      color: 'rgba(255,255,255,0.35)',
      cursor: 'pointer',
      display: 'flex',
      padding: 6,
      borderRadius: 6,
      transition: 'color 0.15s'
    }
  }, /*#__PURE__*/React.createElement(IconSidebarClose, {
    size: 17
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      fontFamily: DS.fonts.mono,
      fontSize: 13,
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: DS.colors.orange2
    }
  }, "SecureAI"), /*#__PURE__*/React.createElement(IconChevronRight, {
    size: 11
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      color: DS.colors.textPrimary
    }
  }, viewMode === 'editor' ? 'UserAuth.java' : 'Security Dashboard')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 5,
      marginLeft: 8
    }
  }, /*#__PURE__*/React.createElement(PipelinePill, {
    label: "SAST",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
    border: "rgba(34,197,94,0.35)"
  }), /*#__PURE__*/React.createElement(PipelinePill, {
    label: "DAST",
    color: "#f97316",
    bg: "rgba(249,115,22,0.10)",
    border: "rgba(249,115,22,0.30)"
  }), /*#__PURE__*/React.createElement(PipelinePill, {
    label: "PATCH",
    color: "#818cf8",
    bg: "rgba(99,102,241,0.10)",
    border: "rgba(99,102,241,0.30)"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setSeverityFilter('all'),
    style: {
      fontSize: 10,
      fontWeight: 800,
      fontFamily: DS.fonts.mono,
      padding: '3px 9px',
      borderRadius: 4,
      cursor: 'pointer',
      background: severityFilter === 'all' ? 'rgba(255,255,255,0.12)' : 'transparent',
      color: severityFilter === 'all' ? DS.colors.textPrimary : 'rgba(255,255,255,0.3)',
      border: `1px solid ${severityFilter === 'all' ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)'}`,
      transition: 'all 0.15s'
    }
  }, "ALL"), SEV_FILTERS.map(sev => {
    const active = severityFilter === sev;
    const c = SEV_COLORS[sev];
    return /*#__PURE__*/React.createElement("button", {
      key: sev,
      onClick: () => setSeverityFilter(active ? 'all' : sev),
      style: {
        fontSize: 10,
        fontWeight: 800,
        fontFamily: DS.fonts.mono,
        padding: '3px 9px',
        borderRadius: 4,
        cursor: 'pointer',
        background: active ? c : `${c}22`,
        color: active ? '#fff' : c,
        border: `1px solid ${active ? c : `${c}55`}`,
        transition: 'all 0.15s'
      }
    }, sev.toUpperCase());
  })), /*#__PURE__*/React.createElement("button", {
    onClick: () => setViewMode(v => v === 'editor' ? 'dashboard' : 'editor'),
    style: {
      fontSize: 11,
      fontWeight: 700,
      padding: '5px 12px',
      borderRadius: 6,
      background: DS.colors.bg3,
      color: DS.colors.textPrimary,
      border: `1px solid ${DS.colors.border2}`,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      transition: 'all 0.15s'
    }
  }, viewMode === 'editor' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconDashboard, {
    size: 13
  }), " \uB300\uC2DC\uBCF4\uB4DC") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconCode, {
    size: 13
  }), " \uC5D0\uB514\uD130")), /*#__PURE__*/React.createElement("button", {
    onClick: startAnalysis,
    disabled: isAnalyzing,
    style: {
      fontSize: 11,
      fontWeight: 800,
      padding: '6px 16px',
      borderRadius: 6,
      background: isAnalyzing ? 'rgba(234,88,12,0.35)' : DS.colors.orange2,
      color: '#fff',
      border: 'none',
      cursor: isAnalyzing ? 'not-allowed' : 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      boxShadow: isAnalyzing ? 'none' : '0 3px 12px rgba(234,88,12,0.4)',
      transition: 'all 0.15s'
    }
  }, isAnalyzing ? /*#__PURE__*/React.createElement(IconSpin, {
    size: 12
  }) : /*#__PURE__*/React.createElement(IconPlay, {
    size: 12
  }), isAnalyzing ? '분석 중...' : '분석 시작'), /*#__PURE__*/React.createElement("button", {
    style: {
      fontSize: 10,
      fontWeight: 500,
      color: DS.colors.textTertiary,
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconFileJson, {
    size: 13
  }), " Export JSON")));
}
Object.assign(window, {
  AppHeader
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/AppHeader.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/AppSidebar.jsx
try { (() => {
// SecureAI — AppSidebar component
const {
  useState
} = React;
const FILE_TREE = [{
  name: 'my-spring-project',
  path: '/',
  type: 'dir',
  expanded: true,
  children: [{
    name: 'src/main/java',
    path: '/src/main/java',
    type: 'dir',
    expanded: true,
    children: [{
      name: 'UserAuth.java',
      path: '/src/main/java/UserAuth.java',
      type: 'file',
      vulnCount: 3,
      severity: 'critical'
    }, {
      name: 'PaymentSvc.java',
      path: '/src/main/java/PaymentSvc.java',
      type: 'file',
      vulnCount: 1,
      severity: 'high'
    }, {
      name: 'OrderAPI.java',
      path: '/src/main/java/OrderAPI.java',
      type: 'file',
      vulnCount: 0,
      severity: null
    }, {
      name: 'FileUpload.java',
      path: '/src/main/java/FileUpload.java',
      type: 'file',
      vulnCount: 2,
      severity: 'high'
    }]
  }, {
    name: 'src/main/resources',
    path: '/src/main/resources',
    type: 'dir',
    expanded: false,
    children: [{
      name: 'config.properties',
      path: '/src/main/resources/config.properties',
      type: 'file',
      vulnCount: 1,
      severity: 'medium'
    }]
  }]
}];
function FileNode({
  node,
  depth = 0,
  selectedPath,
  onSelect,
  expanded,
  onToggle
}) {
  const isDir = node.type === 'dir';
  const isSelected = !isDir && selectedPath === node.path;
  const isExpanded = expanded[node.path];
  const SEV_COLORS = {
    critical: '#f04141',
    high: '#f59e0b',
    medium: '#eab308',
    low: '#22c55e'
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("button", {
    onClick: () => isDir ? onToggle(node.path) : onSelect(node.path),
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      padding: `4px 10px 4px ${12 + depth * 14}px`,
      background: isSelected ? 'rgba(234,88,12,0.12)' : 'transparent',
      border: 'none',
      cursor: 'pointer',
      textAlign: 'left',
      borderLeft: isSelected ? '2px solid #ea580c' : '2px solid transparent',
      transition: 'all 0.12s'
    },
    onMouseEnter: e => {
      if (!isSelected) e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
    },
    onMouseLeave: e => {
      if (!isSelected) e.currentTarget.style.background = 'transparent';
    }
  }, isDir && /*#__PURE__*/React.createElement("span", {
    style: {
      color: DS.colors.textTertiary,
      flexShrink: 0,
      display: 'flex'
    }
  }, isExpanded ? /*#__PURE__*/React.createElement(IconChevronDown, {
    size: 10
  }) : /*#__PURE__*/React.createElement(IconChevronRight, {
    size: 10
  })), isDir ? /*#__PURE__*/React.createElement(IconFolder, {
    size: 12
  }) : /*#__PURE__*/React.createElement(IconFile, {
    size: 12
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 11,
      color: isSelected ? DS.colors.orange : isDir ? DS.colors.textSecondary : DS.colors.textPrimary,
      flex: 1,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }
  }, node.name), !isDir && node.vulnCount > 0 && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 9,
      fontWeight: 700,
      flexShrink: 0,
      color: SEV_COLORS[node.severity] || DS.colors.textTertiary,
      background: `${SEV_COLORS[node.severity]}18`,
      padding: '1px 5px',
      borderRadius: 3
    }
  }, node.vulnCount)), isDir && isExpanded && node.children?.map(child => /*#__PURE__*/React.createElement(FileNode, {
    key: child.path,
    node: child,
    depth: depth + 1,
    selectedPath: selectedPath,
    onSelect: onSelect,
    expanded: expanded,
    onToggle: onToggle
  })));
}
function AppSidebar({
  sidebarOpen,
  selectedPath,
  setSelectedPath,
  setViewMode,
  isAnalyzing,
  startAnalysis,
  viewMode
}) {
  const [expanded, setExpanded] = useState({
    '/': true,
    '/src/main/java': true
  });
  const toggleDir = path => setExpanded(prev => ({
    ...prev,
    [path]: !prev[path]
  }));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: sidebarOpen ? 240 : 0,
      flexShrink: 0,
      background: DS.colors.bg1,
      borderRight: `1px solid ${DS.colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      transition: 'width 0.15s'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 14px',
      borderBottom: `1px solid ${DS.colors.border}`,
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement(IconShield, {
    size: 14,
    color: "#f97316"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: '0.12em',
      color: 'rgba(255,255,255,0.4)',
      textTransform: 'uppercase'
    }
  }, "SecureAI")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '7px 12px 5px',
      fontSize: 9,
      fontFamily: DS.fonts.mono,
      fontWeight: 700,
      letterSpacing: '0.15em',
      textTransform: 'uppercase',
      color: DS.colors.textTertiary,
      borderBottom: `1px solid rgba(255,255,255,0.04)`,
      flexShrink: 0
    }
  }, "\uD504\uB85C\uC81D\uD2B8 \uD30C\uC77C (MCP)"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: 'auto',
      paddingTop: 4
    }
  }, FILE_TREE.map(node => /*#__PURE__*/React.createElement(FileNode, {
    key: node.path,
    node: node,
    selectedPath: selectedPath,
    onSelect: p => {
      setSelectedPath(p);
      setViewMode('editor');
    },
    expanded: expanded,
    onToggle: toggleDir
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 10,
      borderTop: `1px solid ${DS.colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: startAnalysis,
    disabled: isAnalyzing,
    style: {
      width: '100%',
      padding: '8px 0',
      background: DS.colors.orange2,
      border: 'none',
      borderRadius: 7,
      color: '#fff',
      fontSize: 11,
      fontWeight: 700,
      cursor: isAnalyzing ? 'not-allowed' : 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 5,
      boxShadow: '0 3px 12px rgba(234,88,12,0.3)',
      opacity: isAnalyzing ? 0.7 : 1,
      transition: 'all 0.15s'
    }
  }, isAnalyzing ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconSpin, {
    size: 11
  }), " \uBD84\uC11D \uC911...") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconPlay, {
    size: 11,
    color: "#fff"
  }), " \uC804\uCCB4 \uD504\uB85C\uC81D\uD2B8 \uBD84\uC11D")), /*#__PURE__*/React.createElement("button", {
    onClick: () => setViewMode(v => v === 'editor' ? 'dashboard' : 'editor'),
    style: {
      width: '100%',
      padding: '6px 0',
      background: 'rgba(255,255,255,0.05)',
      border: `1px solid rgba(255,255,255,0.08)`,
      borderRadius: 7,
      color: DS.colors.textSecondary,
      fontSize: 11,
      fontWeight: 600,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 5,
      transition: 'all 0.15s'
    }
  }, viewMode === 'editor' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconDashboard, {
    size: 11
  }), " \uB300\uC2DC\uBCF4\uB4DC") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(IconCode, {
    size: 11
  }), " \uC5D0\uB514\uD130")), /*#__PURE__*/React.createElement("button", {
    style: {
      width: '100%',
      padding: '6px 0',
      background: 'transparent',
      border: `1px solid rgba(255,255,255,0.06)`,
      borderRadius: 7,
      color: DS.colors.textTertiary,
      fontSize: 11,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement(IconGithub, {
    size: 11
  }), " GitHub \uC5F0\uB3D9")));
}
Object.assign(window, {
  AppSidebar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/AppSidebar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/Dashboard.jsx
try { (() => {
// SecureAI — Dashboard v2 (improved)
const {
  useState,
  useMemo
} = React;
const STATS = {
  score: 62,
  critical: 3,
  high: 7,
  medium: 3,
  low: 1,
  patched: 4,
  total: 14,
  scoreChange: +4
};
const TREND = [{
  date: '03/14',
  score: 41
}, {
  date: '03/15',
  score: 47
}, {
  date: '03/16',
  score: 50
}, {
  date: '03/17',
  score: 53
}, {
  date: '03/18',
  score: 58
}, {
  date: '03/19',
  score: 60
}, {
  date: '03/20',
  score: 62
}];
const OWASP = [{
  id: 'A01',
  label: 'Broken Access Control',
  hit: true
}, {
  id: 'A02',
  label: 'Cryptographic Failures',
  hit: true
}, {
  id: 'A03',
  label: 'Injection',
  hit: true
}, {
  id: 'A04',
  label: 'Insecure Design',
  hit: true
}, {
  id: 'A05',
  label: 'Security Misconfig',
  hit: false
}, {
  id: 'A06',
  label: 'Vulnerable Components',
  hit: false
}, {
  id: 'A07',
  label: 'Auth Failures',
  hit: true
}, {
  id: 'A08',
  label: 'Software Integrity',
  hit: false
}, {
  id: 'A09',
  label: 'Security Logging',
  hit: false
}, {
  id: 'A10',
  label: 'SSRF',
  hit: false
}];
const HEATMAP = [{
  file: 'UserAuth.java',
  critical: 3,
  high: 0,
  medium: 1,
  low: 0
}, {
  file: 'FileUpload.java',
  critical: 0,
  high: 2,
  medium: 0,
  low: 0
}, {
  file: 'PaymentSvc.java',
  critical: 0,
  high: 1,
  medium: 0,
  low: 0
}, {
  file: 'OrderAPI.java',
  critical: 0,
  high: 0,
  medium: 0,
  low: 0
}];
const PRS = [{
  num: 42,
  title: 'feature/auth-refactor',
  status: 'fail',
  detail: 'SQL Injection Critical 발견',
  time: '10분 전'
}, {
  num: 41,
  title: 'fix/payment-null-check',
  status: 'pass',
  detail: '취약점 없음',
  time: '1시간 전'
}, {
  num: 40,
  title: 'feat/file-upload',
  status: 'warning',
  detail: 'Path Traversal 2건',
  time: '3시간 전'
}, {
  num: 39,
  title: 'refactor/order-service',
  status: 'pass',
  detail: '취약점 없음',
  time: '1일 전'
}, {
  num: 38,
  title: 'feat/payment-v2',
  status: 'running',
  detail: '분석 중...',
  time: '방금 전'
}];
const PR_COLOR = {
  pass: '#22c55e',
  fail: '#f04141',
  warning: '#f59e0b',
  running: '#569cd6'
};
const PR_LABEL = {
  pass: '통과',
  fail: '실패',
  warning: '경고',
  running: '분석중'
};
function MiniSparkline({
  data,
  color,
  w = 60,
  h = 24
}) {
  const min = Math.min(...data),
    max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = i / (data.length - 1) * w;
    const y = h - (v - min) / range * (h - 4) - 2;
    return `${x},${y}`;
  });
  return /*#__PURE__*/React.createElement("svg", {
    width: w,
    height: h,
    viewBox: `0 0 ${w} ${h}`,
    style: {
      overflow: 'visible'
    }
  }, /*#__PURE__*/React.createElement("polyline", {
    points: pts.join(' '),
    fill: "none",
    stroke: color,
    strokeWidth: "1.5",
    strokeLinejoin: "round",
    opacity: "0.8"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: pts[pts.length - 1].split(',')[0],
    cy: pts[pts.length - 1].split(',')[1],
    r: "2.5",
    fill: color
  }));
}
function KpiStrip() {
  const scoreColor = STATS.score >= 80 ? '#22c55e' : STATS.score >= 60 ? '#f97316' : '#f04141';
  const scoreTrend = TREND.map(d => d.score);
  const cards = [{
    label: '보안 점수',
    value: STATS.score,
    color: scoreColor,
    sub: `전일 대비 +${STATS.scoreChange}`,
    sparkData: scoreTrend,
    isScore: true
  }, {
    label: 'Critical',
    value: STATS.critical,
    color: '#f04141',
    sub: '즉시 조치 필요',
    sparkData: [5, 4, 4, 4, 3, 3, 3]
  }, {
    label: 'High',
    value: STATS.high,
    color: '#f59e0b',
    sub: '강하게 권고',
    sparkData: [9, 8, 8, 8, 7, 7, 7]
  }, {
    label: 'Medium',
    value: STATS.medium,
    color: '#eab308',
    sub: '모니터링 중',
    sparkData: [4, 4, 3, 3, 3, 3, 3]
  }, {
    label: '패치 완료율',
    value: `${Math.round(STATS.patched / STATS.total * 100)}%`,
    color: '#22c55e',
    sub: `${STATS.patched} / ${STATS.total}건`,
    sparkData: [20, 25, 25, 30, 28, 28, 29]
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 10
    }
  }, cards.map((card, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      background: '#111114',
      border: `1px solid #1f1f24`,
      borderRadius: 10,
      padding: '14px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      position: 'relative',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 2,
      background: card.color,
      opacity: 0.7,
      borderRadius: '10px 10px 0 0'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: '#9494a0',
      fontFamily: DS.fonts.mono,
      marginTop: 2
    }
  }, card.label), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-end',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 32,
      fontWeight: 700,
      color: card.color,
      lineHeight: 1,
      letterSpacing: '-0.02em'
    }
  }, card.value), /*#__PURE__*/React.createElement(MiniSparkline, {
    data: card.sparkData,
    color: card.color
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: '#555560',
      fontFamily: DS.fonts.mono
    }
  }, card.sub))));
}
function TrendChart() {
  const w = 420,
    h = 90;
  const min = 30,
    max = 100;
  const pts = TREND.map((d, i) => {
    const x = 20 + i / (TREND.length - 1) * (w - 40);
    const y = h - 10 - (d.score - min) / (max - min) * (h - 20);
    return {
      x,
      y,
      ...d
    };
  });
  const linePts = pts.map(p => `${p.x},${p.y}`).join(' L ');
  const areaPath = `M${pts[0].x},${pts[0].y} L ${linePts} L${pts[pts.length - 1].x},${h - 10} L${pts[0].x},${h - 10} Z`;
  const gridLines = [40, 55, 70, 85, 100];
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("svg", {
    width: "100%",
    viewBox: `0 0 ${w} ${h + 20}`,
    style: {
      overflow: 'visible'
    }
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("linearGradient", {
    id: "tg",
    x1: "0",
    y1: "0",
    x2: "0",
    y2: "1"
  }, /*#__PURE__*/React.createElement("stop", {
    offset: "0%",
    stopColor: "#f97316",
    stopOpacity: "0.25"
  }), /*#__PURE__*/React.createElement("stop", {
    offset: "100%",
    stopColor: "#f97316",
    stopOpacity: "0"
  }))), gridLines.map(v => {
    const y = h - 10 - (v - min) / (max - min) * (h - 20);
    return /*#__PURE__*/React.createElement("g", {
      key: v
    }, /*#__PURE__*/React.createElement("line", {
      x1: 20,
      y1: y,
      x2: w - 20,
      y2: y,
      stroke: "#1f1f24",
      strokeWidth: "1"
    }), /*#__PURE__*/React.createElement("text", {
      x: 14,
      y: y + 3,
      fontSize: "8",
      fill: "#555560",
      textAnchor: "end",
      fontFamily: "JetBrains Mono, monospace"
    }, v));
  }), /*#__PURE__*/React.createElement("path", {
    d: areaPath,
    fill: "url(#tg)"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: pts.map(p => `${p.x},${p.y}`).join(' '),
    fill: "none",
    stroke: "#f97316",
    strokeWidth: "2",
    strokeLinejoin: "round"
  }), pts.map((p, i) => /*#__PURE__*/React.createElement("g", {
    key: i
  }, /*#__PURE__*/React.createElement("circle", {
    cx: p.x,
    cy: p.y,
    r: i === pts.length - 1 ? 5 : 3,
    fill: i === pts.length - 1 ? '#f97316' : '#f97316',
    opacity: i === pts.length - 1 ? 1 : 0.5
  }), i === pts.length - 1 && /*#__PURE__*/React.createElement("circle", {
    cx: p.x,
    cy: p.y,
    r: 9,
    stroke: "#f97316",
    strokeWidth: "1",
    fill: "none",
    opacity: "0.2"
  }))), pts.map((p, i) => /*#__PURE__*/React.createElement("text", {
    key: i,
    x: p.x,
    y: h + 15,
    fontSize: "8",
    fill: "#555560",
    textAnchor: "middle",
    fontFamily: "JetBrains Mono, monospace"
  }, p.date))));
}
function SeverityBars() {
  const rows = [{
    label: 'Injection',
    count: 3,
    max: 5,
    color: '#f04141',
    cat: 'A03'
  }, {
    label: 'Auth Failure',
    count: 7,
    max: 10,
    color: '#f59e0b',
    cat: 'A07'
  }, {
    label: 'XSS',
    count: 2,
    max: 5,
    color: '#f59e0b',
    cat: 'A03'
  }, {
    label: 'Access Control',
    count: 3,
    max: 5,
    color: '#eab308',
    cat: 'A01'
  }, {
    label: 'Misc Config',
    count: 1,
    max: 5,
    color: '#eab308',
    cat: 'A05'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 9
    }
  }, rows.map(row => {
    const pct = row.count / row.max * 100;
    return /*#__PURE__*/React.createElement("div", {
      key: row.label,
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: DS.fonts.mono,
        fontSize: 9,
        color: '#555560',
        width: 28,
        flexShrink: 0
      }
    }, row.cat), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: '#9494a0',
        width: 100,
        flexShrink: 0,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, row.label), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        height: 7,
        background: '#1c1c20',
        borderRadius: 4,
        overflow: 'hidden'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        height: '100%',
        width: `${pct}%`,
        background: row.color,
        borderRadius: 4,
        boxShadow: `0 0 8px ${row.color}66`,
        transition: 'width 0.6s ease-out'
      }
    })), /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: DS.fonts.mono,
        fontSize: 10,
        color: row.color,
        width: 16,
        textAlign: 'right',
        flexShrink: 0
      }
    }, row.count));
  }));
}
function FileHeatmapCard() {
  const totalCols = 6;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, HEATMAP.map(row => {
    const total = row.critical + row.high + row.medium + row.low;
    const segments = [{
      count: row.critical,
      color: '#f04141',
      label: 'C'
    }, {
      count: row.high,
      color: '#f59e0b',
      label: 'H'
    }, {
      count: row.medium,
      color: '#eab308',
      label: 'M'
    }, {
      count: row.low,
      color: '#22c55e',
      label: 'L'
    }].filter(s => s.count > 0);
    return /*#__PURE__*/React.createElement("div", {
      key: row.file,
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 10
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        width: 120,
        fontFamily: DS.fonts.mono,
        fontSize: 11,
        color: '#9494a0',
        flexShrink: 0,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      }
    }, row.file), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        height: 18,
        background: '#161619',
        borderRadius: 4,
        overflow: 'hidden',
        display: 'flex'
      }
    }, total === 0 ? /*#__PURE__*/React.createElement("div", {
      style: {
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 9,
        color: '#404048',
        fontFamily: DS.fonts.mono
      }
    }, "\uCDE8\uC57D\uC810 \uC5C6\uC74C")) : segments.map((seg, i) => {
      const pct = seg.count / STATS.total * 100;
      return /*#__PURE__*/React.createElement("div", {
        key: i,
        title: `${seg.label}: ${seg.count}`,
        style: {
          width: `${Math.max(pct * 2.2, 8)}%`,
          background: seg.color,
          opacity: 0.8,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: i < segments.length - 1 ? 1 : 0,
          boxShadow: `inset 0 0 0 0.5px rgba(0,0,0,0.3)`
        }
      }, /*#__PURE__*/React.createElement("span", {
        style: {
          fontFamily: DS.fonts.mono,
          fontSize: 8,
          fontWeight: 700,
          color: '#fff'
        }
      }, seg.count));
    })), /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: DS.fonts.mono,
        fontSize: 10,
        color: '#555560',
        width: 24,
        textAlign: 'right',
        flexShrink: 0
      }
    }, total || '—'));
  }));
}
function OwaspMatrix() {
  const hit = OWASP.filter(o => o.hit);
  const miss = OWASP.filter(o => !o.hit);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: '#f97316',
      fontFamily: DS.fonts.mono,
      fontWeight: 700
    }
  }, "\uD0D0\uC9C0\uB428 ", hit.length, "/10"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: '#555560',
      fontFamily: DS.fonts.mono
    }
  }, "\xB7"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: '#555560',
      fontFamily: DS.fonts.mono
    }
  }, "\uBBF8\uD0D0\uC9C0 ", miss.length, "/10")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 6
    }
  }, OWASP.map(item => /*#__PURE__*/React.createElement("div", {
    key: item.id,
    style: {
      padding: '8px 6px',
      borderRadius: 6,
      textAlign: 'center',
      background: item.hit ? 'rgba(234,88,12,0.1)' : 'rgba(255,255,255,0.02)',
      border: `1px solid ${item.hit ? 'rgba(234,88,12,0.3)' : 'rgba(255,255,255,0.05)'}`,
      position: 'relative'
    }
  }, item.hit && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 4,
      right: 4,
      width: 5,
      height: 5,
      borderRadius: '50%',
      background: '#f04141',
      boxShadow: '0 0 4px rgba(240,65,65,0.8)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      fontWeight: 700,
      color: item.hit ? '#f97316' : '#404048',
      marginBottom: 3
    }
  }, item.id), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 8,
      color: item.hit ? '#9494a0' : '#404048',
      lineHeight: 1.35
    }
  }, item.label)))));
}
function Dashboard({
  severityFilter,
  setSeverityFilter
}) {
  const [timeRange, setTimeRange] = useState('7d');
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: 'auto',
      background: '#0d0d0f'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '18px 24px',
      maxWidth: 1200,
      margin: '0 auto',
      display: 'flex',
      flexDirection: 'column',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingBottom: 14,
      borderBottom: '1px solid rgba(255,255,255,0.06)'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      color: '#e8e8ee',
      letterSpacing: '-0.02em',
      marginBottom: 3
    }
  }, "Security Audit Dashboard"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 10,
      color: '#555560',
      fontFamily: DS.fonts.mono
    }
  }, "secureai-frontend \xB7 \uB9C8\uC9C0\uB9C9 \uBD84\uC11D: \uBC29\uAE08 \uC804 \xB7 \uCDE8\uC57D\uC810 ", STATS.total, "\uAC1C")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 6,
      overflow: 'hidden'
    }
  }, ['24h', '7d', '30d'].map(r => /*#__PURE__*/React.createElement("button", {
    key: r,
    onClick: () => setTimeRange(r),
    style: {
      fontSize: 10,
      fontWeight: 700,
      fontFamily: DS.fonts.mono,
      padding: '5px 12px',
      border: 'none',
      cursor: 'pointer',
      background: timeRange === r ? '#ea580c' : 'transparent',
      color: timeRange === r ? '#fff' : '#555560',
      transition: 'all 0.15s'
    }
  }, r))), /*#__PURE__*/React.createElement("button", {
    style: {
      fontSize: 10,
      fontWeight: 600,
      fontFamily: DS.fonts.mono,
      padding: '5px 12px',
      borderRadius: 6,
      border: '1px solid #1f1f24',
      background: '#111114',
      color: '#9494a0',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "11",
    height: "11",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "23 4 23 10 17 10"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M20.49 15a9 9 0 1 1-.24-3.06"
  })), "\uC0C8\uB85C\uACE0\uCE68"))), /*#__PURE__*/React.createElement(KpiStrip, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1.7fr',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 10,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: '#9494a0',
      fontFamily: DS.fonts.mono,
      marginBottom: 12
    }
  }, "\uC2EC\uAC01\uB3C4 \uBD84\uD3EC (OWASP)"), /*#__PURE__*/React.createElement(SeverityBars, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 10,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: '#9494a0',
      fontFamily: DS.fonts.mono
    }
  }, "\uBCF4\uC548 \uC810\uC218 \uD2B8\uB80C\uB4DC"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: '#f97316',
      fontFamily: DS.fonts.mono,
      fontWeight: 700
    }
  }, "62 (+4\u2191)")), /*#__PURE__*/React.createElement(TrendChart, null))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 10,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: '#9494a0',
      fontFamily: DS.fonts.mono,
      marginBottom: 12
    }
  }, "\uD30C\uC77C\uBCC4 \uCDE8\uC57D\uC810 \uD788\uD2B8\uB9F5"), /*#__PURE__*/React.createElement(FileHeatmapCard, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1.2fr',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 10,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: '#9494a0',
      fontFamily: DS.fonts.mono,
      marginBottom: 12
    }
  }, "OWASP Top 10 \uCEE4\uBC84\uB9AC\uC9C0"), /*#__PURE__*/React.createElement(OwaspMatrix, null)), /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#111114',
      border: '1px solid #1f1f24',
      borderRadius: 10,
      padding: '14px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 7,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("svg", {
    width: "13",
    height: "13",
    viewBox: "0 0 24 24",
    fill: "currentColor",
    style: {
      color: '#9494a0'
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: '#9494a0',
      fontFamily: DS.fonts.mono
    }
  }, "GitHub PR \uB9AC\uBDF0 \uC774\uB825")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 0
    }
  }, PRS.map((pr, i) => /*#__PURE__*/React.createElement("div", {
    key: pr.num,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 0',
      borderBottom: i < PRS.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: PR_COLOR[pr.status],
      flexShrink: 0,
      boxShadow: `0 0 5px ${PR_COLOR[pr.status]}88`
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      color: '#9494a0',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: '#555560'
    }
  }, "#", pr.num), " ", pr.title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      color: '#555560',
      fontFamily: DS.fonts.mono,
      marginTop: 2
    }
  }, pr.detail)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      fontFamily: DS.fonts.mono,
      fontWeight: 700,
      padding: '2px 6px',
      borderRadius: 3,
      color: PR_COLOR[pr.status],
      background: `${PR_COLOR[pr.status]}18`,
      border: `0.5px solid ${PR_COLOR[pr.status]}44`
    }
  }, PR_LABEL[pr.status]), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: '#404048',
      fontFamily: DS.fonts.mono
    }
  }, pr.time)))))))));
}
Object.assign(window, {
  Dashboard
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/Dashboard.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/EditorPanel.jsx
try { (() => {
// SecureAI — EditorPanel (code viewer + DAST terminal + right panel)
const {
  useState,
  useRef,
  useEffect
} = React;
const FILE_CONTENTS = {
  '/src/main/java/UserAuth.java': `package com.example.auth;
import java.sql.*;

public class UserAuth {
    private static final String DB_URL = "jdbc:mysql://localhost/mydb";
    // WARNING: 하드코딩된 시크릿
    private static final String SECRET = "super_secret_key_1234";

    public User findUserByName(String username) throws SQLException {
        Connection conn = DriverManager.getConnection(DB_URL);
        // CRITICAL: SQL Injection 취약점
        String query = "SELECT * FROM users WHERE name = '" + username + "'";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(query);
        if (rs.next()) {
            return new User(rs.getString("id"), rs.getString("name"));
        }
        return null;
    }

    public boolean verifyToken(String inputToken, String userToken) {
        // HIGH: == 연산자로 문자열 비교 (Broken Auth)
        if (inputToken == userToken) {
            return true;
        }
        return false;
    }

    public void resetPassword(String userId, String newPassword) {
        // MEDIUM: 비밀번호 복잡도 검사 없음
        updatePasswordInDB(userId, newPassword);
    }
}`,
  '/src/main/java/PaymentSvc.java': `package com.example.payment;

public class PaymentSvc {
    public void processPayment(String userId, double amount) {
        // HIGH: 금액 검증 없음
        if (userId != null) {
            executePayment(userId, amount);
        }
    }
    private void executePayment(String userId, double amount) {
        System.out.println("Processing: " + userId + " -> " + amount);
    }
}`,
  '/src/main/java/OrderAPI.java': `package com.example.order;

public class OrderAPI {
    public Order getOrder(String orderId, String userId) {
        Order order = orderRepository.findById(orderId);
        if (order != null && order.getUserId().equals(userId)) {
            return order;
        }
        throw new UnauthorizedException("Access denied");
    }
}`,
  '/src/main/java/FileUpload.java': `package com.example.upload;
import java.io.*;

public class FileUpload {
    // HIGH: 파일 확장자 검증 없음
    public void uploadFile(String fileName, byte[] content) {
        File file = new File("/uploads/" + fileName);
        try (FileOutputStream fos = new FileOutputStream(file)) {
            fos.write(content);
        } catch (IOException e) { e.printStackTrace(); }
    }

    // HIGH: Path Traversal 취약점
    public byte[] downloadFile(String fileName) throws IOException {
        File file = new File("/uploads/" + fileName);
        return java.nio.file.Files.readAllBytes(file.toPath());
    }
}`
};
const VULN_LINES = {
  '/src/main/java/UserAuth.java': {
    12: 'critical',
    13: 'critical',
    14: 'critical',
    6: 'high',
    7: 'high',
    22: 'high',
    23: 'high',
    24: 'high',
    29: 'medium'
  },
  '/src/main/java/PaymentSvc.java': {
    4: 'high',
    5: 'high',
    6: 'high'
  },
  '/src/main/java/FileUpload.java': {
    5: 'high',
    6: 'high',
    15: 'high',
    16: 'high',
    17: 'high'
  }
};
const DAST_LOGS = [{
  t: '10:42:01',
  level: 'info',
  msg: 'Docker 샌드박스 초기화 중...'
}, {
  t: '10:42:02',
  level: 'info',
  msg: '타겟: UserAuth.java → findUserByName()'
}, {
  t: '10:42:03',
  level: 'info',
  msg: "SQL Injection 페이로드 생성 중..."
}, {
  t: '10:42:04',
  level: 'warn',
  msg: "페이로드 #1: ' OR '1'='1' -- 주입 시도"
}, {
  t: '10:42:05',
  level: 'error',
  msg: '[EXPLOIT] 성공: DB 레코드 15개 노출 확인'
}, {
  t: '10:42:06',
  level: 'warn',
  msg: "페이로드 #2: '; DROP TABLE users; -- 주입 시도"
}, {
  t: '10:42:07',
  level: 'error',
  msg: '[EXPLOIT] 성공: DDL 실행 가능 확인'
}, {
  t: '10:42:08',
  level: 'success',
  msg: '패치 제안 생성 완료 → PreparedStatement 적용 권장'
}];
const SEV_BG = {
  critical: 'rgba(240,65,65,0.08)',
  high: 'rgba(245,158,11,0.07)',
  medium: 'rgba(234,179,8,0.07)',
  low: 'rgba(34,197,94,0.07)'
};
const SEV_BAR = {
  critical: '#f04141',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#22c55e'
};
const MOCK_TABS = [{
  path: '/src/main/java/UserAuth.java',
  label: 'UserAuth.java',
  severity: 'critical'
}, {
  path: '/src/main/java/PaymentSvc.java',
  label: 'PaymentSvc.java',
  severity: 'high'
}, {
  path: '/src/main/java/FileUpload.java',
  label: 'FileUpload.java',
  severity: 'high'
}];
function CodeLine({
  num,
  text,
  vuln
}) {
  const c = SEV_BAR[vuln] || null;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      minHeight: 20.8,
      background: vuln ? SEV_BG[vuln] : 'transparent',
      boxShadow: vuln ? `inset 3px 0 0 ${c}` : 'none'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 44,
      flexShrink: 0,
      textAlign: 'right',
      paddingRight: 14,
      userSelect: 'none',
      color: DS.colors.textTertiary,
      fontSize: 12,
      fontFamily: DS.fonts.mono,
      lineHeight: '20.8px'
    }
  }, num), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 12.5,
      color: DS.colors.textPrimary,
      whiteSpace: 'pre',
      lineHeight: '20.8px',
      flex: 1
    }
  }, text));
}
function EditorPanel({
  selectedPath,
  severityFilter
}) {
  const code = FILE_CONTENTS[selectedPath] || '// 파일을 선택하세요';
  const lines = code.split('\n');
  const vulnMap = VULN_LINES[selectedPath] || {};
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      background: DS.colors.bg1,
      borderBottom: `1px solid ${DS.colors.border}`,
      flexShrink: 0
    }
  }, MOCK_TABS.map(tab => {
    const active = tab.path === selectedPath;
    const c = SEV_BAR[tab.severity];
    return /*#__PURE__*/React.createElement("div", {
      key: tab.path,
      style: {
        padding: '6px 14px',
        fontSize: 11.5,
        fontFamily: DS.fonts.mono,
        color: active ? DS.colors.textPrimary : DS.colors.textTertiary,
        borderBottom: `1.5px solid ${active ? DS.colors.orange2 : 'transparent'}`,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        cursor: 'default',
        background: active ? DS.colors.bg2 : 'transparent'
      }
    }, c && /*#__PURE__*/React.createElement("span", {
      style: {
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: c,
        boxShadow: `0 0 5px ${c}aa`,
        flexShrink: 0,
        display: 'inline-block'
      }
    }), tab.label);
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto',
      background: DS.colors.bg2
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 0'
    }
  }, lines.map((line, i) => {
    const lineNum = i + 1;
    const sev = vulnMap[lineNum];
    const sevOk = !severityFilter || severityFilter === 'all' || sev === severityFilter;
    return /*#__PURE__*/React.createElement(CodeLine, {
      key: i,
      num: lineNum,
      text: line,
      vuln: sevOk ? sev : undefined
    });
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 170,
      flexShrink: 0,
      background: '#050507',
      borderTop: `1px solid ${DS.colors.border}`,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '6px 12px',
      borderBottom: `1px solid ${DS.colors.border}`,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      fontWeight: 700,
      color: DS.colors.orange,
      letterSpacing: '0.08em'
    }
  }, "DAST TERMINAL"), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: '#22c55e',
      display: 'inline-block'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '6px 12px',
      overflow: 'auto',
      height: 'calc(100% - 31px)'
    }
  }, DAST_LOGS.map((log, i) => {
    const c = log.level === 'error' ? DS.colors.critical : log.level === 'warn' ? DS.colors.high : log.level === 'success' ? DS.colors.low : DS.colors.textTertiary;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        display: 'flex',
        gap: 8,
        fontFamily: DS.fonts.mono,
        fontSize: 11,
        marginBottom: 2
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        color: DS.colors.textTertiary,
        flexShrink: 0
      }
    }, log.t), /*#__PURE__*/React.createElement("span", {
      style: {
        color: c
      }
    }, log.msg));
  }))));
}
Object.assign(window, {
  EditorPanel
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/EditorPanel.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/RightPanel.jsx
try { (() => {
// SecureAI — RightPanel (VulnList + AI Chat tabs)
const {
  useState
} = React;
const VULNS = [{
  id: 'v1',
  type: 'SQL Injection',
  severity: 'critical',
  lineStart: 12,
  filePath: '/src/main/java/UserAuth.java',
  description: '사용자 입력값을 검증 없이 SQL 쿼리에 직접 삽입. 공격자가 임의의 SQL을 실행하여 DB 전체를 탈취할 수 있습니다.',
  cweId: 'CWE-89',
  owaspCategory: 'A03:2021',
  status: 'exploited',
  dastResult: "' OR '1'='1' -- 페이로드 실행 → DB 레코드 15개 노출 확인",
  apiEndpoint: 'POST /api/users/login',
  apiGroup: '/api/users',
  callChain: [{
    layer: 'Frontend',
    label: 'LoginForm.handleSubmit()',
    file: 'App.tsx',
    line: 18,
    isVulnerable: false
  }, {
    layer: 'Controller',
    label: 'UserController.login()',
    file: 'UserController.java',
    line: 34,
    isVulnerable: false
  }, {
    layer: 'Service',
    label: 'AuthService.authenticate()',
    file: 'AuthService.java',
    line: 22,
    isVulnerable: false
  }, {
    layer: 'Repository',
    label: 'UserAuth.findUserByName()',
    file: 'UserAuth.java',
    line: 12,
    isVulnerable: true
  }],
  patch: {
    original: `String query = "SELECT * FROM users WHERE name = '" + username + "'";`,
    patched: `String query = "SELECT * FROM users WHERE name = ?";\nPreparedStatement stmt = conn.prepareStatement(query);\nstmt.setString(1, username);`,
    explanation: 'PreparedStatement로 SQL Injection 원천 차단'
  }
}, {
  id: 'v2',
  type: 'Hardcoded Secret',
  severity: 'high',
  lineStart: 6,
  filePath: '/src/main/java/UserAuth.java',
  description: 'API 시크릿 키가 소스코드에 하드코딩됨. Git에 커밋되면 외부에 노출됩니다.',
  cweId: 'CWE-798',
  owaspCategory: 'A02:2021',
  status: 'open',
  callChain: null
}, {
  id: 'v3',
  type: 'Broken Authentication',
  severity: 'high',
  lineStart: 21,
  filePath: '/src/main/java/UserAuth.java',
  description: 'Java에서 == 연산자는 문자열 참조를 비교합니다. .equals()를 사용해야 합니다.',
  cweId: 'CWE-287',
  owaspCategory: 'A07:2021',
  status: 'patched',
  callChain: [{
    layer: 'Frontend',
    label: 'TokenRefresh.request()',
    file: 'App.tsx',
    line: 44,
    isVulnerable: false
  }, {
    layer: 'Controller',
    label: 'UserController.verify()',
    file: 'UserController.java',
    line: 56,
    isVulnerable: false
  }, {
    layer: 'Repository',
    label: 'UserAuth.verifyToken()',
    file: 'UserAuth.java',
    line: 21,
    isVulnerable: true
  }]
}, {
  id: 'v4',
  type: 'Weak Password Policy',
  severity: 'medium',
  lineStart: 28,
  filePath: '/src/main/java/UserAuth.java',
  description: '비밀번호 재설정 시 복잡도 검사, 길이 제한 등의 정책이 없습니다.',
  cweId: 'CWE-521',
  owaspCategory: 'A07:2021',
  status: 'open',
  callChain: null
}];
const LAYER_COLOR = {
  Frontend: '#378ADD',
  Controller: '#7F77DD',
  Service: '#1D9E75',
  Repository: '#E24B4A',
  Config: '#BA7517'
};
const SEV_BAR = {
  critical: '#f04141',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#22c55e'
};
const INIT_CHAT = [{
  id: 'm1',
  role: 'ai',
  content: '안녕하세요! SecureAI 보안 에이전트입니다.\n분석할 파일을 선택하거나 궁금한 점을 질문해주세요.'
}, {
  id: 'm2',
  role: 'user',
  content: 'UserAuth.java 파일 분석해줘'
}, {
  id: 'm3',
  role: 'ai',
  content: 'SAST 분석 완료! UserAuth.java에서 3개 취약점을 발견했습니다.\n\nCritical: SQL Injection (Line 12)\nHigh: Hardcoded Secret (Line 6)\nHigh: Broken Auth (Line 21)\n\n가장 심각한 SQL Injection부터 DAST로 검증할까요?'
}];
function VulnCard({
  vuln,
  severityFilter
}) {
  const [open, setOpen] = useState(false);
  const [patched, setPatched] = useState(vuln.status === 'patched');
  const [fixing, setFix] = useState(false);
  const show = !severityFilter || severityFilter === 'all' || vuln.severity === severityFilter;
  if (!show) return null;
  const c = SEV_BAR[vuln.severity];
  const handleFix = () => {
    setFix(true);
    setTimeout(() => {
      setFix(false);
      setPatched(true);
    }, 1400);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: `0.5px solid rgba(255,255,255,0.08)`,
      borderRight: `0.5px solid rgba(255,255,255,0.08)`,
      borderBottom: `0.5px solid rgba(255,255,255,0.08)`,
      borderLeft: `2px solid ${patched ? '#22c55e' : c}`,
      borderRadius: 8,
      background: DS.colors.bg2,
      overflow: 'hidden',
      transition: 'border-color 0.2s'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(v => !v),
    style: {
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '10px 12px',
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement(SeverityBadge, {
    level: vuln.severity
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: patched ? '#22c55e' : DS.colors.textPrimary
    }
  }, patched && '✓ ', vuln.type), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      fontFamily: DS.fonts.mono,
      color: DS.colors.textTertiary,
      marginTop: 1
    }
  }, vuln.filePath.split('/').pop(), ":", vuln.lineStart, vuln.apiEndpoint && /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 8,
      color: 'rgba(249,115,22,0.5)'
    }
  }, vuln.apiEndpoint))), open ? /*#__PURE__*/React.createElement(IconChevronDown, {
    size: 12
  }) : /*#__PURE__*/React.createElement(IconChevronRight, {
    size: 12
  })), open && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px',
      background: 'rgba(0,0,0,0.2)',
      borderTop: `0.5px solid rgba(255,255,255,0.06)`,
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      color: DS.colors.textTertiary,
      marginBottom: 5,
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconInfo, {
    size: 9
  }), " \uC124\uBA85"), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 11,
      lineHeight: 1.7,
      color: 'rgba(232,232,238,0.7)'
    }
  }, vuln.description), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 4,
      marginTop: 5,
      flexWrap: 'wrap'
    }
  }, [vuln.cweId, vuln.owaspCategory].map(t => /*#__PURE__*/React.createElement("span", {
    key: t,
    style: {
      fontSize: 9,
      padding: '1px 6px',
      border: `0.5px solid rgba(255,255,255,0.1)`,
      borderRadius: 3,
      color: DS.colors.textTertiary
    }
  }, t)))), vuln.dastResult && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      color: DS.colors.textTertiary,
      marginBottom: 5,
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconWarning, {
    size: 9
  }), " \uACF5\uACA9 \uC2DC\uB098\uB9AC\uC624"), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '7px 10px',
      background: 'rgba(249,115,22,0.06)',
      border: `0.5px solid rgba(249,115,22,0.15)`,
      borderRadius: 6,
      fontSize: 11,
      color: 'rgba(253,186,116,0.8)',
      fontStyle: 'italic',
      lineHeight: 1.6,
      fontFamily: DS.fonts.mono
    }
  }, vuln.dastResult)), vuln.callChain?.length > 0 && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      color: DS.colors.textTertiary,
      marginBottom: 8,
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconLayers, {
    size: 9
  }), " API \uD638\uCD9C \uCCB4\uC778"), vuln.callChain.map((step, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: 12,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      marginTop: 3,
      flexShrink: 0,
      background: step.isVulnerable ? '#E24B4A' : 'rgba(255,255,255,0.2)',
      boxShadow: step.isVulnerable ? '0 0 10px rgba(226,75,74,0.8)' : 'none'
    }
  }), i < vuln.callChain.length - 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      width: 1,
      flex: 1,
      minHeight: 18,
      background: 'rgba(255,255,255,0.06)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      paddingBottom: 10,
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 8,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: LAYER_COLOR[step.layer] || DS.colors.textTertiary,
      marginBottom: 1
    }
  }, step.layer), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      fontWeight: 700,
      color: step.isVulnerable ? '#E24B4A' : 'rgba(255,255,255,0.7)',
      fontFamily: DS.fonts.mono
    }
  }, step.label, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 400,
      color: DS.colors.textTertiary,
      fontSize: 9
    }
  }, "\xB7 ", step.file, ":", step.line, " ", /*#__PURE__*/React.createElement(IconExternalLink, {
    size: 7
  }))))))), vuln.patch && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
      color: DS.colors.textTertiary,
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconZap, {
    size: 9
  }), " \uD328\uCE58 \uC81C\uC548"), !patched ? /*#__PURE__*/React.createElement("button", {
    onClick: handleFix,
    disabled: fixing,
    style: {
      fontSize: 10,
      padding: '3px 10px',
      background: '#16a34a',
      border: 'none',
      borderRadius: 4,
      color: '#fff',
      fontWeight: 700,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: 4,
      boxShadow: '0 2px 8px rgba(22,163,74,0.3)'
    }
  }, fixing ? /*#__PURE__*/React.createElement(IconSpin, {
    size: 10
  }) : /*#__PURE__*/React.createElement(IconZap, {
    size: 10
  }), " AUTO FIX") : /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: '#22c55e',
      display: 'flex',
      alignItems: 'center',
      gap: 3
    }
  }, /*#__PURE__*/React.createElement(IconCheck, {
    size: 10
  }), " \uC801\uC6A9\uB428")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      color: '#f04141',
      marginBottom: 3,
      opacity: 0.7
    }
  }, "Before"), /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#050505',
      borderRadius: 5,
      border: `0.5px solid rgba(240,65,65,0.2)`,
      padding: '6px 8px',
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      color: '#f87171',
      lineHeight: 1.7,
      whiteSpace: 'pre-wrap'
    }
  }, vuln.patch.original)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      color: '#22c55e',
      marginBottom: 3,
      opacity: 0.7
    }
  }, "After"), /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#050505',
      borderRadius: 5,
      border: `0.5px solid rgba(76,175,80,0.2)`,
      padding: '6px 8px',
      fontFamily: DS.fonts.mono,
      fontSize: 10,
      color: '#86efac',
      lineHeight: 1.7,
      whiteSpace: 'pre-wrap'
    }
  }, vuln.patch.patched))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 5,
      fontSize: 10,
      color: 'rgba(76,175,80,0.7)',
      display: 'flex',
      alignItems: 'center',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(IconCheck, {
    size: 9
  }), " ", vuln.patch.explanation))));
}
function FilterBar({
  severityFilter,
  setSeverityFilter
}) {
  const filters = ['critical', 'high', 'medium', 'low'];
  const SEV_COL = {
    critical: '#f04141',
    high: '#f59e0b',
    medium: '#eab308',
    low: '#22c55e'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px 10px',
      borderBottom: `1px solid ${DS.colors.border}`,
      display: 'flex',
      gap: 4,
      flexWrap: 'wrap',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setSeverityFilter('all'),
    style: {
      fontSize: 9,
      fontWeight: 800,
      fontFamily: DS.fonts.mono,
      padding: '3px 8px',
      borderRadius: 3,
      cursor: 'pointer',
      background: severityFilter === 'all' ? 'rgba(255,255,255,0.12)' : 'transparent',
      color: severityFilter === 'all' ? DS.colors.textPrimary : DS.colors.textTertiary,
      border: `1px solid ${severityFilter === 'all' ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)'}`
    }
  }, "ALL"), filters.map(s => {
    const active = severityFilter === s;
    const c = SEV_COL[s];
    return /*#__PURE__*/React.createElement("button", {
      key: s,
      onClick: () => setSeverityFilter(active ? 'all' : s),
      style: {
        fontSize: 9,
        fontWeight: 800,
        fontFamily: DS.fonts.mono,
        padding: '3px 8px',
        borderRadius: 3,
        cursor: 'pointer',
        background: active ? c : `${c}22`,
        color: active ? '#fff' : c,
        border: `1px solid ${active ? c : `${c}55`}`
      }
    }, s.toUpperCase());
  }));
}
function ChatPanel() {
  const [messages, setMessages] = useState(INIT_CHAT);
  const [input, setInput] = useState('');
  const bottom = useRef(null);
  useEffect(() => {
    bottom.current?.scrollIntoView && (bottom.current.scrollTop = bottom.current.scrollHeight);
  }, [messages]);
  const send = () => {
    const t = input.trim();
    if (!t) return;
    const id = `m${Date.now()}`;
    setMessages(prev => [...prev, {
      id,
      role: 'user',
      content: t
    }]);
    setInput('');
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: id + 'r',
        role: 'ai',
        content: '분석 중입니다. 잠시 기다려주세요...'
      }]);
    }, 600);
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    ref: bottom,
    style: {
      flex: 1,
      overflowY: 'auto',
      padding: '10px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, messages.map(msg => /*#__PURE__*/React.createElement("div", {
    key: msg.id,
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
    }
  }, msg.role === 'ai' && /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      marginBottom: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 16,
      height: 16,
      borderRadius: '50%',
      background: DS.colors.orange2,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 7,
      fontWeight: 800,
      color: '#fff'
    }
  }, "AI"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: DS.colors.textTertiary,
      fontFamily: DS.fonts.mono
    }
  }, "SecureAI")), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: '85%',
      padding: '8px 10px',
      borderRadius: msg.role === 'user' ? '8px 8px 2px 8px' : '8px 8px 8px 2px',
      background: msg.role === 'user' ? DS.colors.orange2 : DS.colors.bg3,
      fontSize: 11,
      lineHeight: 1.6,
      color: DS.colors.textPrimary,
      whiteSpace: 'pre-wrap'
    }
  }, msg.content)))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '8px',
      borderTop: `1px solid ${DS.colors.border}`,
      flexShrink: 0,
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: input,
    onChange: e => setInput(e.target.value),
    onKeyDown: e => e.key === 'Enter' && send(),
    placeholder: "\uC9C8\uBB38\uD558\uAE30...",
    style: {
      flex: 1,
      background: DS.colors.bg3,
      border: `1px solid ${DS.colors.border}`,
      borderRadius: 5,
      padding: '6px 10px',
      fontSize: 11,
      color: DS.colors.textPrimary,
      fontFamily: DS.fonts.sans,
      outline: 'none'
    }
  }), /*#__PURE__*/React.createElement("button", {
    onClick: send,
    style: {
      background: DS.colors.orange2,
      border: 'none',
      borderRadius: 5,
      color: '#fff',
      width: 30,
      fontSize: 14,
      cursor: 'pointer',
      fontWeight: 700
    }
  }, "\u2191")));
}
function RightPanel({
  severityFilter,
  setSeverityFilter
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: 300,
      flexShrink: 0,
      background: DS.colors.bg1,
      borderLeft: `1px solid ${DS.colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '10px 14px 8px',
      borderBottom: `1px solid ${DS.colors.border}`,
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(IconShieldAlert, {
    size: 13
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: DS.colors.textPrimary
    }
  }, "\uCDE8\uC57D\uC810 (", VULNS.length, ")")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement(FilterBar, {
    severityFilter: severityFilter,
    setSeverityFilter: setSeverityFilter
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: 'auto',
      padding: '8px',
      display: 'flex',
      flexDirection: 'column',
      gap: 5
    }
  }, VULNS.map(v => /*#__PURE__*/React.createElement(VulnCard, {
    key: v.id,
    vuln: v,
    severityFilter: severityFilter
  })))));
}
Object.assign(window, {
  RightPanel
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/RightPanel.jsx", error: String((e && e.message) || e) }); }

// ui_kits/editor/Shared.jsx
try { (() => {
// SecureAI Design System — Shared Tokens & Utilities
// Load BEFORE other components with <script type="text/babel" src="Shared.jsx">

const DS = {
  colors: {
    bg0: '#080809',
    bg1: '#0d0d0f',
    bg2: '#111114',
    bg3: '#161619',
    bg4: '#1c1c20',
    border: '#1f1f24',
    border2: '#2a2a30',
    textPrimary: '#e8e8ee',
    textSecondary: '#9494a0',
    textTertiary: '#555560',
    textDisabled: '#404048',
    orange: '#f97316',
    orange2: '#ea580c',
    critical: '#f04141',
    high: '#f59e0b',
    medium: '#eab308',
    low: '#22c55e',
    info: '#569cd6',
    layerFE: '#378ADD',
    layerCtrl: '#7F77DD',
    layerSvc: '#1D9E75',
    layerRepo: '#E24B4A',
    layerCfg: '#BA7517'
  },
  fonts: {
    sans: "'Space Grotesk', system-ui, sans-serif",
    mono: "'JetBrains Mono', 'Consolas', monospace"
  }
};
const SEV_COLOR = {
  critical: '#f04141',
  high: '#f59e0b',
  medium: '#eab308',
  low: '#22c55e',
  info: '#569cd6'
};
function SeverityBadge({
  level
}) {
  const c = SEV_COLOR[level] || '#9494a0';
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
      padding: '2px 6px',
      borderRadius: 3,
      color: c,
      background: `${c}18`,
      border: `1px solid ${c}40`
    }
  }, level);
}
function SeverityDot({
  level,
  size = 8
}) {
  const c = SEV_COLOR[level] || '#9494a0';
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-block',
      width: size,
      height: size,
      borderRadius: '50%',
      background: c,
      boxShadow: `0 0 6px ${c}99`,
      flexShrink: 0
    }
  });
}
function PipelinePill({
  label,
  color,
  bg,
  border
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: DS.fonts.mono,
      fontSize: 9,
      fontWeight: 800,
      padding: '2px 8px',
      borderRadius: 10,
      background: bg,
      color,
      border: `0.5px solid ${border}`
    }
  }, label);
}
function IconShield({
  size = 16,
  color = '#f97316'
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
  }));
}
function IconPlay({
  size = 14,
  color = 'currentColor'
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: color,
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polygon", {
    points: "5,3 19,12 5,21"
  }));
}
function IconCode({
  size = 14
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "16 18 22 12 16 6"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "8 6 2 12 8 18"
  }));
}
function IconDashboard({
  size = 14
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "3",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "14",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "14",
    width: "7",
    height: "7"
  }));
}
function IconChevronRight({
  size = 12
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "9 18 15 12 9 6"
  }));
}
function IconChevronDown({
  size = 12
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "6 9 12 15 18 9"
  }));
}
function IconFolder({
  size = 13,
  open = false
}) {
  return open ? /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "#9494a0",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
  })) : /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "#9494a0",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
  }));
}
function IconFile({
  size = 13
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "#9494a0",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "13 2 13 9 20 9"
  }));
}
function IconGithub({
  size = 12
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "currentColor",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"
  }));
}
function IconSpin({
  size = 12
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true",
    style: {
      animation: 'spin 0.85s linear infinite'
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M21 12a9 9 0 1 1-6.219-8.56"
  }));
}
function IconShieldAlert({
  size = 13
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "8",
    x2: "12",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "16",
    x2: "12.01",
    y2: "16"
  }));
}
function IconChat({
  size = 13
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
  }));
}
function IconZap({
  size = 12
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polygon", {
    points: "13 2 3 14 12 14 11 22 21 10 12 10 13 2"
  }));
}
function IconCheck({
  size = 11
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2.5",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "20 6 9 17 4 12"
  }));
}
function IconLayers({
  size = 11
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("polygon", {
    points: "12 2 2 7 12 12 22 7 12 2"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "2 17 12 22 22 17"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "2 12 12 17 22 12"
  }));
}
function IconInfo({
  size = 10
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "16",
    x2: "12",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "8",
    x2: "12.01",
    y2: "8"
  }));
}
function IconWarning({
  size = 10
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "9",
    x2: "12",
    y2: "13"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "17",
    x2: "12.01",
    y2: "17"
  }));
}
function IconExternalLink({
  size = 9
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "15 3 21 3 21 9"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "10",
    y1: "14",
    x2: "21",
    y2: "3"
  }));
}
function IconFileJson({
  size = 13
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "14 2 14 8 20 8"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M10 12a1 1 0 0 0-1 1v1a1 1 0 0 1-1 1 1 1 0 0 1 1 1v1a1 1 0 0 0 1 1"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M14 18a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1 1 1 0 0 1-1-1v-1a1 1 0 0 0-1-1"
  }));
}
function IconSidebarClose({
  size = 18
}) {
  return /*#__PURE__*/React.createElement("svg", {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "18",
    height: "18",
    rx: "2"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "9",
    y1: "3",
    x2: "9",
    y2: "21"
  }));
}
Object.assign(window, {
  DS,
  SEV_COLOR,
  SeverityBadge,
  SeverityDot,
  PipelinePill,
  IconShield,
  IconPlay,
  IconCode,
  IconDashboard,
  IconChevronRight,
  IconChevronDown,
  IconFolder,
  IconFile,
  IconGithub,
  IconSpin,
  IconShieldAlert,
  IconChat,
  IconZap,
  IconCheck,
  IconLayers,
  IconInfo,
  IconWarning,
  IconExternalLink,
  IconFileJson,
  IconSidebarClose
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/editor/Shared.jsx", error: String((e && e.message) || e) }); }

})();
