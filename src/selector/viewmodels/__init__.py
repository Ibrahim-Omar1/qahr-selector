"""viewmodels — MVVM bridges (QObject) between the engine and the views.

Expose engine state as Qt signals/properties and turn UI intents into service
calls. The UI never touches the engine directly; it binds to view-models.
"""
