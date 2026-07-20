# RxJava/Coroutines to BLoC — reactive pattern dictionary

**What this is.** A reactive-pattern translation aid: a lookup table that helps the AI read
RxJava/Coroutines idioms in legacy Android code and map each one to its BLoC equivalent (or to a
Mermaid diagram annotation) without hallucinating a state that isn't there. Used while synthesizing
the state machine from `extraction-prompt.template.md`'s output.

**Caveat:** this is a starter set — 4 patterns, the ones observed so far. Extend the table as new
legacy operators turn up in real targets; do not invent additional rows speculatively.

| Padrão Legado (Kotlin / RxJava) | Conversão para BLoC (Flutter) / Mermaid |
| --- | --- |
| `doOnSubscribe { showLoading.postValue(true) }` | Dispara o estado inicial de transição: `LoadingState` |
| `.subscribe( { data -> ... }, { error -> ... } )` | Bifurcação de estado: `SuccessState` vs `FailureState` |
| `.debounce(300, TimeUnit.MILLISECONDS)` | **Atenção do Arquiteto:** Isso não é estado, é transformação de evento. Anotar no diagrama: `Event Transformer (Debounce)` |
| `onErrorResumeNext { Observable.just(CacheState) }` | Fallback de rede. Transição de erro mapeada para `SuccessState(CachedData)`. |
