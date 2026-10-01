"""Features of communications (completeness contract, PD-F003-B01)."""

from core.features import Feature, Lifecycle, provided, register_feature

register_feature(
    Feature(
        key="message",
        label="Message",
        model="communications.Message",
        claims={"identity": provided("field:public_id")},
        lifecycle=Lifecycle(
            "none",
            note=(
                "Created once when sent and never edited; "
                "recipients are rows beside it (MessageRecipient)."
            ),
        ),
    )
)
