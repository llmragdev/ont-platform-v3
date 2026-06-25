const STORAGE_KEY = "temp-board-posts-v1";

const categoryLabels = {
  notice: "공지",
  task: "할 일",
  meeting: "회의",
  idea: "아이디어",
};

const seedPosts = [
  {
    id: crypto.randomUUID(),
    title: "임시 게시판 사용 안내",
    author: "관리자",
    category: "notice",
    pinned: true,
    body: "이 게시판은 브라우저 localStorage에 글을 저장합니다.\n\n새 글, 수정, 삭제, 검색, 분류 필터를 사용할 수 있습니다.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: crypto.randomUUID(),
    title: "워크플로우 논의 메모",
    author: "Codex",
    category: "meeting",
    pinned: false,
    body: "템플릿을 복제해서 수정하는 방식으로 워크플로우를 구성하는 방향을 검토했습니다.",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
];

let posts = loadPosts();
let selectedId = posts[0]?.id ?? null;

const els = {
  postList: document.querySelector("#postList"),
  detailPanel: document.querySelector("#detailPanel"),
  totalCount: document.querySelector("#totalCount"),
  pinnedCount: document.querySelector("#pinnedCount"),
  todayCount: document.querySelector("#todayCount"),
  searchInput: document.querySelector("#searchInput"),
  categoryFilter: document.querySelector("#categoryFilter"),
  newPostButton: document.querySelector("#newPostButton"),
  postDialog: document.querySelector("#postDialog"),
  postForm: document.querySelector("#postForm"),
  dialogTitle: document.querySelector("#dialogTitle"),
  closeDialogButton: document.querySelector("#closeDialogButton"),
  cancelButton: document.querySelector("#cancelButton"),
  postId: document.querySelector("#postId"),
  titleInput: document.querySelector("#titleInput"),
  authorInput: document.querySelector("#authorInput"),
  categoryInput: document.querySelector("#categoryInput"),
  pinnedInput: document.querySelector("#pinnedInput"),
  bodyInput: document.querySelector("#bodyInput"),
};

els.searchInput.addEventListener("input", render);
els.categoryFilter.addEventListener("change", render);
els.newPostButton.addEventListener("click", () => openEditor());
els.closeDialogButton.addEventListener("click", closeEditor);
els.cancelButton.addEventListener("click", closeEditor);
els.postForm.addEventListener("submit", savePostFromForm);

render();

function loadPosts() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(seedPosts));
    return seedPosts;
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : seedPosts;
  } catch {
    return seedPosts;
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(posts));
}

function render() {
  renderSummary();
  renderList();
  renderDetail();
}

function renderSummary() {
  const today = new Date().toDateString();
  els.totalCount.textContent = posts.length;
  els.pinnedCount.textContent = posts.filter((post) => post.pinned).length;
  els.todayCount.textContent = posts.filter((post) => {
    return new Date(post.createdAt).toDateString() === today;
  }).length;
}

function renderList() {
  const filtered = getFilteredPosts();
  els.postList.innerHTML = "";

  if (filtered.length === 0) {
    els.postList.innerHTML = '<div class="empty-list">조건에 맞는 글이 없습니다.</div>';
    return;
  }

  for (const post of filtered) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `post-item ${post.id === selectedId ? "active" : ""}`;
    button.innerHTML = `
      <div class="post-meta">
        ${post.pinned ? '<span class="badge pin">중요</span>' : ""}
        <span class="badge ${post.category}">${categoryLabels[post.category]}</span>
        <span>${escapeHtml(post.author)}</span>
        <span>${formatDate(post.updatedAt)}</span>
      </div>
      <h3>${escapeHtml(post.title)}</h3>
      <p class="preview">${escapeHtml(truncate(post.body, 92))}</p>
    `;
    button.addEventListener("click", () => {
      selectedId = post.id;
      render();
    });
    els.postList.append(button);
  }
}

function renderDetail() {
  const post = posts.find((item) => item.id === selectedId);
  if (!post) {
    els.detailPanel.innerHTML = `
      <div class="empty-state">
        <h3>게시글을 선택하세요</h3>
        <p>왼쪽 목록에서 글을 선택하거나 새 글을 작성할 수 있습니다.</p>
      </div>
    `;
    return;
  }

  els.detailPanel.innerHTML = `
    <header class="detail-header">
      <div>
        <div class="post-meta">
          ${post.pinned ? '<span class="badge pin">중요</span>' : ""}
          <span class="badge ${post.category}">${categoryLabels[post.category]}</span>
          <span>${escapeHtml(post.author)}</span>
          <span>작성 ${formatDate(post.createdAt)}</span>
          <span>수정 ${formatDate(post.updatedAt)}</span>
        </div>
        <h3>${escapeHtml(post.title)}</h3>
      </div>
      <div class="detail-actions">
        <button class="secondary-button" type="button" data-action="edit">수정</button>
        <button class="danger-button" type="button" data-action="delete">삭제</button>
      </div>
    </header>
    <div class="detail-body">${escapeHtml(post.body)}</div>
  `;

  els.detailPanel.querySelector('[data-action="edit"]').addEventListener("click", () => openEditor(post));
  els.detailPanel.querySelector('[data-action="delete"]').addEventListener("click", () => deletePost(post.id));
}

function getFilteredPosts() {
  const query = els.searchInput.value.trim().toLowerCase();
  const category = els.categoryFilter.value;

  return [...posts]
    .filter((post) => category === "all" || post.category === category)
    .filter((post) => {
      if (!query) return true;
      return [post.title, post.author, post.body].some((value) => value.toLowerCase().includes(query));
    })
    .sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
}

function openEditor(post = null) {
  els.dialogTitle.textContent = post ? "글 수정" : "새 글 작성";
  els.postId.value = post?.id ?? "";
  els.titleInput.value = post?.title ?? "";
  els.authorInput.value = post?.author ?? "사용자";
  els.categoryInput.value = post?.category ?? "notice";
  els.pinnedInput.checked = Boolean(post?.pinned);
  els.bodyInput.value = post?.body ?? "";
  els.postDialog.showModal();
  els.titleInput.focus();
}

function closeEditor() {
  els.postDialog.close();
  els.postForm.reset();
}

function savePostFromForm(event) {
  event.preventDefault();

  const now = new Date().toISOString();
  const id = els.postId.value || crypto.randomUUID();
  const existing = posts.find((post) => post.id === id);
  const next = {
    id,
    title: els.titleInput.value.trim(),
    author: els.authorInput.value.trim(),
    category: els.categoryInput.value,
    pinned: els.pinnedInput.checked,
    body: els.bodyInput.value.trim(),
    createdAt: existing?.createdAt ?? now,
    updatedAt: now,
  };

  if (existing) {
    posts = posts.map((post) => (post.id === id ? next : post));
  } else {
    posts = [next, ...posts];
  }

  selectedId = id;
  persist();
  closeEditor();
  render();
}

function deletePost(id) {
  const post = posts.find((item) => item.id === id);
  if (!post) return;
  const ok = confirm(`"${post.title}" 글을 삭제할까요?`);
  if (!ok) return;

  posts = posts.filter((item) => item.id !== id);
  selectedId = posts[0]?.id ?? null;
  persist();
  render();
}

function formatDate(value) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function truncate(value, max) {
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
