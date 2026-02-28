from rest_framework.throttling import AnonRateThrottle


class LibraryListThrottle(AnonRateThrottle):
    scope = 'library_list'


class LibraryCreateThrottle(AnonRateThrottle):
    scope = 'library_create'


class LibraryDetailThrottle(AnonRateThrottle):
    scope = 'library_detail'


class LibraryUpdateThrottle(AnonRateThrottle):
    scope = 'library_update'


class LibraryDeleteThrottle(AnonRateThrottle):
    scope = 'library_delete'


class LibraryStatsThrottle(AnonRateThrottle):
    scope = 'library_stats'
