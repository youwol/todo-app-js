const cdnClient = window["@youwol/cdn-client"];

const { FluxView, HttpClients } = await cdnClient.install({
  modules: ["@youwol/flux-view", "@youwol/http-clients"],
  css: [
    "bootstrap#4.4.1~bootstrap.min.css",
    "fontawesome#5.12.1~css/all.min.css",
    "@youwol/fv-widgets#latest~dist/assets/styles/style.youwol.css",
  ],
  aliases: {
    FluxView: "@youwol/flux-view",
    HttpClients: "@youwol/http-clients",
  },
});

const { CdnSessionsStorage } = HttpClients;

const { BehaviorSubject, combineLatest } = window.rxjs;
const { map, mergeMap, skip } = window.rxjs.operators;

const classes = {
  chevron: "fas fa-chevron-down p-2 fa-2x text-secondary",
  itemViewContainer:
    "d-flex align-items-center justify-content-between item-view",
  itemCheckContainer:
    "border rounded-circle m-2 d-flex flex-column justify-content-center item-check-container",
  itemDelete: "delete fas fa-times text-danger float-right px-3",
  itemSuccess: "fas fa-check mx-auto text-success",
  footer: "d-flex align-items-center px-3 border-top py-2 text-secondary",
};

const Filter = {
  ALL: 1,
  ACTIVE: 2,
  COMPLETED: 3,
};

class AppState {
  static STORAGE_KEY = "todo-list";
  client = new CdnSessionsStorage.Client();
  constructor() {
    this.items$ = new BehaviorSubject([]);

    this.client
      .getData$({
        packageName: "@youwol/todo-app-js",
        dataName: AppState.STORAGE_KEY,
      })
      .subscribe((d) => {
        this.items$.next(d.items ? d.items : []);
      });
    this.items$
      .pipe(
        skip(1),
        mergeMap((items) =>
          this.client.postData$({
            packageName: "@youwol/todo-app-js",
            dataName: AppState.STORAGE_KEY,
            body: { items },
          }),
        ),
      )
      .subscribe(() => {
        console.log("data saved");
      });

    this.completed$ = this.items$.pipe(
      map((items) => items.reduce((acc, item) => acc && item.done, true)),
    );
    this.remaining$ = this.items$.pipe(
      map((items) => items.filter((item) => !item.done)),
    );
    this.filterMode$ = new BehaviorSubject(Filter.ALL);
    this.filterFcts = {
      [Filter.ALL]: () => true,
      [Filter.ACTIVE]: (item) => !item.done,
      [Filter.COMPLETED]: (item) => item.done,
    };
    this.selectedItems$ = combineLatest([this.items$, this.filterMode$]).pipe(
      map(([items, mode]) =>
        items.filter((item) => this.filterFcts[mode](item)),
      ),
    );
  }

  toggleAll() {
    const completed = this.getItems().reduce(
      (acc, item) => acc && item.done,
      true,
    );
    this.items$.next(
      this.getItems().map((item) => ({
        id: item.id,
        name: item.name,
        done: !completed,
      })),
    );
  }

  addItem(name) {
    const item = { id: Date.now(), name, completed: false };
    this.items$.next([...this.getItems(), item]);
    return item;
  }

  deleteItem(id) {
    this.items$.next(this.getItems().filter((item) => item.id !== id));
  }

  toggleItem(id) {
    const items = this.getItems().map((item) =>
      item.id === id
        ? { id: item.id, name: item.name, done: !item.done }
        : item,
    );
    this.items$.next(items);
  }

  setName(id, name) {
    const items = this.getItems().map((item) =>
      item.id === id ? { id: item.id, name, done: item.done } : item,
    );
    this.items$.next(items);
  }

  getItems() {
    return this.items$.getValue();
  }

  setFilter(mode) {
    this.filterMode$.next(mode);
  }
}

class HeaderView {
  tag = "header";
  class = "header";

  constructor(appState) {
    this.children = [
      {
        tag: "h1",
        innerText: "todos",
      },
      {
        class: " d-flex align-items-center",
        children: [
          {
            tag: "i",
            class: FluxView.attr$(
              appState.completed$,
              (completed) => (completed ? "text-dark" : "text-light"),
              { wrapper: (d) => `${d} ${classes.chevron}` },
            ),
            onclick: () => appState.toggleAll(),
          },
          {
            tag: "input",
            autofocus: "autofocus",
            autocomplete: "off",
            placeholder: "What needs to be done?",
            class: "new-todo",
            onkeypress: (ev) => {
              ev.key === "Enter" &&
                appState.addItem(ev.target.value) &&
                (ev.target.value = "");
            },
          },
        ],
      },
    ];
  }
}

class ItemEditionView {
  tag = "input";
  type = "text";
  onclick = (ev) => ev.stopPropagation();
  onkeypress = (ev) => {
    if (ev.key === "Enter") {
      // otherwise the onblur event is triggered while the element does not exist anymore
      ev.target.onblur = () => {};
      this.appState.setName(this.item.id, ev.target.value);
    }
  };
  onblur = (ev) => this.appState.setName(this.item.id, ev.target.value);

  constructor(item, appState) {
    Object.assign(this, { item, appState });
  }
}

class ItemPresentationView {
  tag = "span";
  ondblclick = () => this.edited$.next(true);

  constructor(item, edited$) {
    Object.assign(this, { edited$ });

    this.innerText = item.name;
    this.class = item.done ? "text-muted" : "text-dark";
    this.style = {
      font: "24px 'Helvetica Neue', Helvetica, Arial, sans-serif",
      "text-decoration": item.done ? "line-through" : "",
    };
  }
}

class ItemView {
  tag = "header";
  class = classes.itemViewContainer;
  edited$ = new window.rxjs.BehaviorSubject(false);

  constructor(item, appState) {
    this.children = [
      {
        class: classes.itemCheckContainer,
        onclick: () => appState.toggleItem(item.id),
        children: [{ class: item.done ? classes.itemSuccess : "" }],
      },
      FluxView.child$(
        this.edited$,
        (edited) =>
          edited
            ? new ItemEditionView(item, appState)
            : new ItemPresentationView(item, this.edited$),
        { sideEffects: (_, elem) => elem.focus() },
      ),
      {
        tag: "i",
        class: classes.itemDelete,
        onclick: () => appState.deleteItem(item.id),
      },
    ];
  }
}

class FooterView {
  class = classes.footer;

  constructor(appState) {
    const class$ = (target) =>
      FluxView.attr$(
        appState.filterMode$,
        (mode) => (mode === target ? "selected" : ""),
        { wrapper: (d) => `${d} mx-2 fv-pointer ` },
      );

    this.children = [
      {
        tag: "span",
        innerText: FluxView.attr$(
          appState.remaining$,
          (items) => items.length,
          { wrapper: (d) => `${d} item${d > 1 ? "s" : ""} left` },
        ),
      },
      {
        class: "d-flex align-items-center mx-auto",
        children: [
          {
            innerText: "All",
            class: class$(Filter.ALL),
            onclick: () => appState.setFilter(Filter.ALL),
          },
          {
            innerText: "Active",
            class: class$(Filter.ACTIVE),
            onclick: () => appState.setFilter(Filter.ACTIVE),
          },
          {
            innerText: "Completed",
            class: class$(Filter.COMPLETED),
            onclick: () => appState.setFilter(Filter.COMPLETED),
          },
        ],
      },
    ];
  }
}

class HelpView {
  children = [
    {
      tag: "p",
      class: "text-center",
      innerText: "Double click on an item to edit",
    },
    {
      tag: "p",
      class: "text-center",
      innerHTML:
        "This is a reproduction of the <a href='https://codesandbox.io/s/github/vuejs/vuejs.org/tree/master/src/v2/examples/vue-20-todomvc?from-embed'>todos example of Vue</a>",
    },
  ];
}

class AppView {
  tag = "section";
  class = "todo-app";

  constructor(appState) {
    this.children = [
      new HeaderView(appState),
      {
        children: FluxView.children$(appState.selectedItems$, (items) =>
          items.map((item) => new ItemView(item, appState)),
        ),
      },
      new FooterView(appState),
    ];
  }
}

const state = new AppState();

const div = FluxView.render({
  children: [new AppView(state), new HelpView()],
});
document.getElementById("flux-view").appendChild(div);
