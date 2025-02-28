import opengate_core as g4
import opengate as gate


class TrackCreatorProcessFilter(g4.GateTrackCreatorProcessFilter, gate.UserElement):
    type_name = "TrackCreatorProcessFilter"

    def set_default_user_info(user_info):
        gate.UserElement.set_default_user_info(user_info)
        # required user info, default values
        user_info.process_name = "none"
        user_info.policy = "keep"  # or "discard"

    def __init__(self, user_info):
        g4.GateTrackCreatorProcessFilter.__init__(self)  # no argument in cpp side
        gate.UserElement.__init__(self, user_info)
        # type_name MUST be defined in class that inherit from a Filter
        if user_info.policy != "keep" and user_info.policy != "discard":
            gate.fatal(
                f'TrackCreatorProcessFilter "{user_info.name}" policy must be either "keep" '
                f'or "discard", while it is "{user_info.policy}"'
            )

    def __getstate__(self):
        # needed to not pickle the g4.GateTrackCreatorProcessFilter
        return self.__dict__
