# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Crush map parser..

Parse crush map in json format, and identify storage groups from ruleset.

"""
import json

class CrushMap():

    def __init__(self, json_file):
        with open(json_file, 'r') as fh:
            crush_map = json.load(fh)
            self._tunables = crush_map['tunables']
            self._devices = crush_map['devices']
            self._rules = crush_map['rules']
            self._types = crush_map['types']
            self._buckets = crush_map['buckets']
        pass

    def get_all_tunables(self):
        return self._tunables

    def get_tunable_value(self, parameter):
        return self._tunables[parameter]

    def get_all_types(self):
        return self._types

    def get_type_by_name(self, typename):
        return filter(lambda item: typename == item['name'], self._types)[0]

    def get_all_buckets(self):
        return self._buckets

    def get_bucket_by_id(self, id):
        return filter(lambda item: id == item['id'], self._buckets)[0]

    def get_buckets_by_type(self, typename):
        type = self.get_type_by_name(typename)
        if type:
            type_id = type['type_id']
            return filter(lambda item: type_id == item['type_id'], self._buckets)
        else:
            return []

    def get_buckets_by_name(self, name):
        for bucket in self._buckets:
            if name == bucket['name']:
                return bucket

    def get_children_by_type(self, id, type):
        children = []
        bucket = self.get_bucket_by_id(id)

        for item in bucket['items']:
            child = self.get_bucket_by_id(item['id'])
            if type == child['type_name']:
                children.append(child)

        return children

    def get_all_rules(self):
        return self._rules

    def get_rules_by_name(self, name):
        for rule in self._rules:
            if name == rule['rule_name']:
                return rule

    def get_osd_by_id(self, id):
        osd = filter(lambda item: id == item['id'], self._devices)
        if osd:
            return osd[0]

    def get_all_osds_by_rule(self, name):
        rule = self.get_rules_by_name(name)
        steps = rule['steps']
        for step in steps:
            if step['op'] == 'take':
                bucket = step['item_name']
                print bucket

    def get_all_osds_by_bucket(self, id, devices):
        print id
        if id >=0 :
            osd = self.get_osd_by_id(id)
            devices.append(osd)
        else :
            bucket = self.get_bucket_by_id(id)
            if bucket :
                items = bucket['items']
                for item in items:
                    self.get_all_osds_by_bucket(item['id'], devices)

        return devices

    def get_storage_groups_by_rule(self, rule):
        '''
        this function will execute each op.in detail,
            - op: take  --> the start of an new search
            - op: chooseleaf_firstn/... --> the rule to search
            - op: emit --> the end of a search
        '''
        storage_groups = []
        buckets = []
        sg_count = 0

        for step in rule['steps']:
            op = step['op']
            if op == 'take':
                sg_count += 1
                storage_groups.append([])
                buckets.append(self.get_bucket_by_id(step['item']))

            if op in ['choose_firstn', 'chooseleaf_firstn', 'choose_indep', 'chooseleaf_indep']:
                type = step['type']
                children = []
                for bucket in buckets:
                    temp_buckets = self.get_children_by_type(bucket['id'], type)
                    for temp_bucket in temp_buckets:
                        children.append(temp_bucket)

                buckets = children

            if op == 'emit':
                if sg_count <= 0 :
                    raise "invalid crush map format, take and emit is not in pair"
                for bucket in buckets:
                    devices = []
                    storage_groups[sg_count-1] = self.get_all_osds_by_bucket(bucket['id'],devices)

        print storage_groups
        return storage_groups

if __name__ == '__main__':
    crushmap = CrushMap("./crush.json")

    tunables = crushmap.get_all_tunables()

#    for name in tunables:
#        print name, tunables[name]
#    print crushmap.get_tunable_value('profile')
#    buckets = crushmap.get_all_buckets()
#    bucket = crushmap.get_buckets_by_name('ceph01_high_performance_test_zone0')
#    print bucket

#    print crushmap.get_all_types()
#    print crushmap.get_all_buckets()
#    buckets = crushmap.get_buckets_by_type('zone')
#    print type(buckets)

#    print crushmap.get_rules_by_name('capacity')
#    crushmap.get_all_osds_by_rule('capacity')
#    print crushmap.get_bucket_by_id(-15)

#    print crushmap.get_rules_by_name('performance')

#    print crushmap.get_all_osds_by_bucket(-15, [])
#    bucket = crushmap.get_bucket_by_id(-15)
#    print bucket
#    print crushmap.get_children_by_type(-15, 'zone')
    rule = crushmap.get_rules_by_name('value')
    crushmap.get_storage_groups_by_rule(rule)
