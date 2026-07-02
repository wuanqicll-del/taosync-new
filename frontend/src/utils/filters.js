import {
	parseTime,
	parseSize
} from "@/utils/utils";
import taskItemStatus from '@/utils/taskItemStatus';
import taskStatus from '@/utils/taskStatus';
import notifyMethod from '@/utils/notifyMethod';

const timeStampFilter = (value) => {
	return value ? parseTime(value) : '--';
}

const fmtTime = (value) => {
	return value ? parseTime(value, '{y}-{m}-{d} {h}:{i}') : '--';
}

const taskStatusFilter = (value) => {
	if (value != null) {
		return taskStatus[value];
	} else {
		return '--';
	}
}

const sizeFilter = (val) => {
	return val !== null ? parseSize(val) : '--';
}

const notifyMethodFilter = (val) => {
	if (val != null) {
		return notifyMethod[val];
	} else {
		return '--';
	}
}

const taskItemStatusFilter = (value) => {
	if (value != null) {
		return taskItemStatus[value];
	} else {
		return '--';
	}
}

export default {
	timeStampFilter,
	fmtTime,
	taskStatusFilter,
	taskItemStatusFilter,
	sizeFilter,
	notifyMethodFilter
}