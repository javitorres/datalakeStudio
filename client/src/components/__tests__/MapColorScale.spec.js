import { mount } from '@vue/test-utils'
import MapColorScale from '../MapColorScale.vue'

function scale(props = {}) {
  return mount(MapColorScale, {
    props: { min: 0, max: 100, low: 20, high: 80, histogram: [1, 0, 4, 2], colorLow: '#ffeda0', colorHigh: '#e31a1c', ...props },
  })
}

describe('MapColorScale', () => {
  it('draws the histogram with a bar for each bin that has values', () => {
    const wrapper = scale()
    const bars = wrapper.findAll('rect')
    expect(bars).toHaveLength(4)
    expect(bars.map((bar) => Number(bar.attributes('height')) > 0)).toEqual([true, false, true, true])
    // The gradient spans the chosen range
    const gradient = wrapper.find('linearGradient')
    expect(gradient.attributes('x1')).toBe('20')
    expect(gradient.attributes('x2')).toBe('80')
  })

  it('keeps the low end below the high end', async () => {
    const wrapper = scale()
    const [low, high] = wrapper.findAll('input[type="number"]')
    await low.setValue('95')
    expect(wrapper.emitted('update:low').at(-1)).toEqual([80])
    expect(wrapper.emitted('change')).toHaveLength(1)
    await high.setValue('10')
    expect(wrapper.emitted('update:high').at(-1)).toEqual([20])
  })

  it('changes the colors and asks for the automatic range', async () => {
    const wrapper = scale()
    const [lowColor] = wrapper.findAll('input[type="color"]')
    await lowColor.setValue('#000000')
    expect(wrapper.emitted('update:colorLow')).toEqual([['#000000']])
    await wrapper.find('.scale-reset').trigger('click')
    expect(wrapper.emitted('reset')).toHaveLength(1)
  })
})
