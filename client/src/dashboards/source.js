// Where a dashboard gets its rows from: the user's own engine, or the server for a published one.
// A source has widget(widget, state) and filter(filter), both returning rows.
import { queryPublished } from '../lib/dashboards';
import { filterInfoSql, widgetSql } from './compile';

export function engineSource(engine, spec) {
  return {
    widget: (widget, state) => engine.query(widgetSql(spec, widget, state)),
    filter: (filter) => engine.query(filterInfoSql(spec, filter)),
  };
}

export function publishedSource(path) {
  return {
    widget: (widget, state) => queryPublished(path, widget.id, state),
    filter: (filter) => queryPublished(path, filter.id),
  };
}
