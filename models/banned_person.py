"""
A model of a banned person that mimics the database schema
"""

class BannedPerson:
    """
    A banned person is someone who has been banned from a store
    """
    def __init__(self, full_name, drivers_license,
                 est_value_stolen, reporting_store_id,
                 report_date, is_private, description, id=None):

        self.full_name = full_name
        self.drivers_license = drivers_license
        self.est_value_stolen = est_value_stolen
        self.reporting_store_id = reporting_store_id
        self.report_date = report_date
        self.is_private = is_private
        self.description = description
        self.id = id

    def __str__(self):
        return f"BannedPerson: {self.full_name} {self.drivers_license} \
        {self.est_value_stolen} {self.reporting_store_id} \
        {self.report_date} {self.is_private} {self.description} \
        {self.id}"
    